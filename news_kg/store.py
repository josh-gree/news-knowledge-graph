import hashlib
from collections.abc import Iterable
from pathlib import Path

from news_kg.models import Article


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class FilesystemStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, article_id: str) -> Path:
        return self.root / f"{article_id}.json"

    def save(self, article: Article) -> str:
        article_id = _article_id(article.url)
        path = self._path(article_id)

        if path.exists():
            stored = Article.model_validate_json(path.read_text())
            enrichments = {
                "temporal": article.temporal,
                "entities": article.entities,
            }
            merged = stored.model_copy(
                update={k: v for k, v in enrichments.items() if v is not None}
            )
            path.write_text(merged.model_dump_json())
        else:
            path.write_text(article.model_dump_json())

        return article_id

    def exists(self, article_id: str) -> bool:
        return self._path(article_id).exists()

    def load(self, article_id: str) -> Article:
        path = self._path(article_id)
        if not path.exists():
            raise KeyError(f"Article not found: {article_id}")
        return Article.model_validate_json(path.read_text())

    def all(self) -> Iterable[Article]:
        for path in self.root.glob("*.json"):
            yield Article.model_validate_json(path.read_text())
