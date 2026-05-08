from pathlib import Path

from anthropic import Anthropic
from anthropic.pagination import SyncPage
from anthropic.types.beta import DeletedFile, FileMetadata

from messaging import add_user_message, chat

client = Anthropic()


def upload(file_path: str | Path) -> FileMetadata:
    path = Path(file_path)
    extension = path.suffix.lower()

    mime_type_map = {
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".md": "text/plain",
        ".py": "text/plain",
        ".js": "text/plain",
        ".html": "text/plain",
        ".css": "text/plain",
        ".csv": "text/csv",
        ".json": "application/json",
        ".xml": "application/xml",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xls": "application/vnd.ms-excel",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }

    mime_type = mime_type_map.get(extension)

    if not mime_type:
        raise ValueError(f"Unknown mimetype for extension: {extension}")
    filename = path.name

    with open(file_path, "rb") as file:
        return client.beta.files.upload(file=(filename, file, mime_type))


def list_files() -> SyncPage[FileMetadata]:
    return client.beta.files.list()


def delete_file(id: str) -> DeletedFile:
    return client.beta.files.delete(id)


def download_file(id: str, filename: str | None = None) -> None:
    file_content = client.beta.files.download(id)

    if not filename:
        file_metadata = get_metadata(id)
        file_content.write_to_file(file_metadata.filename)
    else:
        file_content.write_to_file(filename)


def get_metadata(id: str) -> FileMetadata:
    return client.beta.files.retrieve_metadata(id)


file_metadata = upload("streaming.csv")
print(file_metadata.model_dump_json(indent=2))

messages = add_user_message(
    [],
    [
        {
            "type": "text",
            "text": """
            Run a detailed analysis to determine major drivers of churn.
            Your final output should include at least one detailed plot summarizing your findings.

            Critical note: Every time you execute code, you're starting with a completely clean slate. 
            No variables or library imports from previous executions exist. You need to redeclare/reimport all variables/libraries.
            """,
        },
        {"type": "container_upload", "file_id": file_metadata.id},
    ],
)

message = chat(
    messages,
    max_tokens=10000,
    tools=[{"type": "code_execution_20250825", "name": "code_execution"}],
)
print(message.model_dump_json(indent=2))
