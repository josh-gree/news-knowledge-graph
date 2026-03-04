import hashlib
from collections.abc import Iterator
from pathlib import Path

from news_kg.models import AnyArticle, Article, article_adapter


def _article_id(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


class FilesystemStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._articles = root / "articles"
        self._articles.mkdir(parents=True, exist_ok=True)

    def _path(self, article_id: str) -> Path:
        return self._articles / f"{article_id}.json"

    def save(self, article: Article) -> str:
        article_id = _article_id(article.url)
        self._path(article_id).write_text(article.model_dump_json())
        return article_id

    def exists(self, article_id: str) -> bool:
        return self._path(article_id).exists()

    def load(self, article_id: str) -> AnyArticle:
        path = self._path(article_id)
        if not path.exists():
            raise KeyError(f"Article not found: {article_id}")
        return article_adapter.validate_json(path.read_text())

    def all(self) -> Iterator[AnyArticle]:
        for path in self._articles.glob("*.json"):
            yield article_adapter.validate_json(path.read_text())
