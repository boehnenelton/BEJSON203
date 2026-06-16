"""
Library:      lib_md_errors.py
Family:       Markdown (Lib_MD)
Jurisdiction: ["BEJSON_LIBRARIES", "PY"]
Status:       OFFICIAL
Author:       Elton Boehnen
Version:      1.0.0 OFFICIAL
              MFDB Version: 1.31
Format_Creator: Elton Boehnen
Date:         2026-06-15
Description:  Custom exception classes for the lib_bejson_markdown library.
RELATIONAL_ID: md-lib-errors-20260615-001
"""

# --- Error Codes (reserved range: 70–89 for Lib_MD) ---

E_MD_CHUNK_NOT_FOUND      = 70  # chunk_id not in index
E_MD_FILE_NOT_FOUND       = 71  # target markdown file missing
E_MD_INDEX_NOT_FOUND      = 72  # index document missing or unreadable
E_MD_CHUNK_DRIFT          = 73  # checksum mismatch — file edited out-of-band
E_MD_INDEX_STALE          = 74  # index not reindexed after known file write
E_MD_WRITE_FAILED         = 75  # atomic write to markdown file failed
E_MD_INJECT_RANGE_INVALID = 76  # start_line / end_line out of bounds
E_MD_ASSEMBLE_EMPTY       = 77  # assemble returned no chunks (all inactive or no match)
E_MD_MFDB_ERROR           = 78  # MFDB wrapper layer error
E_MD_INVALID_DOCUMENT     = 79  # loaded BEJSON doc fails structural check


class MarkdownLibError(Exception):
    """Base class for all lib_bejson_markdown errors."""
    def __init__(self, message: str, code: int = None):
        super().__init__(message)
        self.code = code


class ChunkNotFoundError(MarkdownLibError):
    """Raised when a chunk_id is not present in the active index."""
    def __init__(self, chunk_id: str):
        super().__init__(f"Chunk not found: '{chunk_id}'", E_MD_CHUNK_NOT_FOUND)
        self.chunk_id = chunk_id


class FileNotFoundError(MarkdownLibError):
    """Raised when the target markdown file does not exist on disk."""
    def __init__(self, file_path: str):
        super().__init__(f"Markdown file not found: '{file_path}'", E_MD_FILE_NOT_FOUND)
        self.file_path = file_path


class IndexNotFoundError(MarkdownLibError):
    """Raised when the BEJSON index document is missing or cannot be loaded."""
    def __init__(self, index_path: str):
        super().__init__(f"Index not found or unreadable: '{index_path}'", E_MD_INDEX_NOT_FOUND)
        self.index_path = index_path


class ChunkDriftError(MarkdownLibError):
    """
    Raised when a chunk's stored checksum does not match the current file content.
    Indicates out-of-band edits to the markdown file. Caller must reindex.
    """
    def __init__(self, chunk_id: str, file_path: str, stored: str, actual: str):
        super().__init__(
            f"Chunk drift detected for '{chunk_id}' in '{file_path}'. "
            f"Stored checksum: {stored} | Actual: {actual}. Reindex required.",
            E_MD_CHUNK_DRIFT
        )
        self.chunk_id   = chunk_id
        self.file_path  = file_path
        self.stored     = stored
        self.actual     = actual


class IndexStaleError(MarkdownLibError):
    """Raised when the index is known to be stale after a failed write sequence."""
    def __init__(self, file_path: str):
        super().__init__(
            f"Index is stale for file '{file_path}'. Run reindex before reading.",
            E_MD_INDEX_STALE
        )
        self.file_path = file_path


class WriteFailedError(MarkdownLibError):
    """Raised when the atomic write to the markdown file fails."""
    def __init__(self, file_path: str, reason: str = ""):
        msg = f"Atomic write failed for '{file_path}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, E_MD_WRITE_FAILED)
        self.file_path = file_path


class InjectRangeInvalidError(MarkdownLibError):
    """Raised when start_line or end_line is out of bounds for the target file."""
    def __init__(self, chunk_id: str, start_line: int, end_line: int, file_lines: int):
        super().__init__(
            f"Inject range invalid for chunk '{chunk_id}': "
            f"[{start_line}:{end_line}] out of bounds for file with {file_lines} lines.",
            E_MD_INJECT_RANGE_INVALID
        )
        self.chunk_id   = chunk_id
        self.start_line = start_line
        self.end_line   = end_line
        self.file_lines = file_lines


class AssembleEmptyError(MarkdownLibError):
    """Raised when assemble returns no chunks — either all inactive or no tag match."""
    def __init__(self, reason: str = ""):
        msg = "Assemble returned no chunks"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, E_MD_ASSEMBLE_EMPTY)


class MFDBWrapperError(MarkdownLibError):
    """Raised when the MFDB wrapper layer encounters an error."""
    def __init__(self, message: str):
        super().__init__(f"MFDB wrapper error: {message}", E_MD_MFDB_ERROR)


class InvalidDocumentError(MarkdownLibError):
    """Raised when a loaded BEJSON document fails structural validation."""
    def __init__(self, path: str, reason: str = ""):
        msg = f"Invalid BEJSON document at '{path}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, E_MD_INVALID_DOCUMENT)
        self.path = path
