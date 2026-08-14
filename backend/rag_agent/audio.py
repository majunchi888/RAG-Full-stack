from pathlib import Path

import os

import yt_dlp
from pydub import AudioSegment

from funasr import AutoModel
from funasr.utils.postprocess_utils import rich_transcription_postprocess

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentChunker:

    def __init__(
        self,
        chunk_size: int = 200,
        chunk_overlap: int = 20,
    ):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        self._asr_model = None

    # =========================================================
    # 对外唯一入口
    # =========================================================

    def create_chunks(self, source: str) -> list[Document]:
        """
        支持：

        PDF
        DOCX
        TXT
        MP3
        WAV
        M4A
        FLAC
        MP4
        AVI
        MOV
        MKV
        WEBM
        YouTube / Bilibili URL

        最终统一返回 list[Document]
        """

        # URL
        if source.startswith(("http://", "https://")):
            return self._process_url(source)

        path = Path(source)
        suffix = path.suffix.lower()

        # 文档
        if suffix == ".pdf":
            return self._process_document(
                source,
                PyPDFLoader(source),
                "pdf",
            )

        if suffix == ".docx":
            return self._process_document(
                source,
                Docx2txtLoader(source),
                "docx",
            )

        if suffix == ".txt":
            return self._process_document(
                source,
                TextLoader(source, encoding="utf-8"),
                "txt",
            )

        # 音频 / 视频
        if suffix in {
            ".mp3",
            ".wav",
            ".m4a",
            ".flac",
            ".aac",
            ".ogg",
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".webm",
        }:
            return self._process_media(source)

        raise ValueError(f"不支持的文件类型: {suffix}")

    # =========================================================
    # PDF / DOCX / TXT
    # =========================================================

    def _process_document(
        self,
        source: str,
        loader,
        file_type: str,
    ) -> list[Document]:

        docs = loader.load()

        for doc in docs:
            doc.metadata["source"] = Path(source).name
            doc.metadata["file_type"] = file_type

        return self.text_splitter.split_documents(docs)

    # =========================================================
    # 音频 / 视频
    # =========================================================

    def _process_media(self, source: str) -> list[Document]:

        print(f"检测到媒体文件：{Path(source).name}")

        wav_path = self._convert_to_wav(source)

        transcript = self._transcribe(wav_path)

        return self._split_text(
            transcript,
            source=source,
            file_type=self._get_media_type(source),
        )

    # =========================================================
    # URL
    # =========================================================

    def _process_url(self, url: str) -> list[Document]:

        print("检测到视频链接，开始下载音频...")

        wav_path = self._download_audio(url)

        transcript = self._transcribe(wav_path)

        return self._split_text(
            transcript,
            source=url,
            file_type="video",
        )

    # =========================================================
    # 下载 YouTube / Bilibili 音频
    # =========================================================

    def _download_audio(self, url: str) -> str:

        os.makedirs("./downloads", exist_ok=True)

        output_path = "./downloads/%(title)s.%(ext)s"

        ydl_opts = {
            "outtmpl": output_path,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "192",
                }
            ],
            "quiet": True,
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        return (
            filename
            .replace(".webm", ".wav")
            .replace(".m4a", ".wav")
        )

    # =========================================================
    # 音视频 → WAV
    # =========================================================

    def _convert_to_wav(self, source: str) -> str:

        output_path = str(
            Path(source).with_name(
                Path(source).stem + "_convert.wav"
            )
        )

        audio = AudioSegment.from_file(source)

        audio = (
            audio
            .set_channels(1)
            .set_frame_rate(16000)
        )

        audio.export(output_path, format="wav")

        return output_path

    # =========================================================
    # SenseVoice
    # =========================================================

    def _load_asr_model(self):

        if self._asr_model is None:

            print("加载 SenseVoice 模型...")

            self._asr_model = AutoModel(
                model=os.getenv(
                    "FUNASR_MODEL",
                    "iic/SenseVoiceSmall",
                ),
                vad_model="fsmn-vad",
                vad_kwargs={
                    "max_single_segment_time": 30000
                },
                device="cuda:0",
                disable_update=True,
            )

            print("SenseVoice 模型加载完成。")

        return self._asr_model

    def _transcribe(self, wav_path: str) -> str:

        model = self._load_asr_model()

        print("开始转录...")

        result = model.generate(
            input=wav_path,
            language="auto",
            use_itn=True,
            merge_vad=True,
            ban_emo_unk=True,
        )

        text = rich_transcription_postprocess(
            result[0]["text"]
        )

        print("转录完成。")

        return text

    # =========================================================
    # transcript → chunks
    # =========================================================

    def _split_text(
        self,
        text: str,
        source: str,
        file_type: str,
    ) -> list[Document]:

        document = Document(
            page_content=text,
            metadata={
                "source": (
                    Path(source).name
                    if not source.startswith(("http://", "https://"))
                    else source
                ),
                "file_type": file_type,
            },
        )

        return self.text_splitter.split_documents(
            [document]
        )

    # =========================================================
    # 工具
    # =========================================================

    @staticmethod
    def _get_media_type(source: str) -> str:

        suffix = Path(source).suffix.lower()

        audio_suffixes = {
            ".mp3",
            ".wav",
            ".m4a",
            ".flac",
            ".aac",
            ".ogg",
        }

        if suffix in audio_suffixes:
            return "audio"

        return "video"