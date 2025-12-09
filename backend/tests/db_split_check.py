import unittest
from pathlib import Path
from sqlalchemy import text

from app.database import engine, AsyncSessionLocal
from app.integrations.vector_store import get_vector_store


class DBIsolationCheck(unittest.IsolatedAsyncioTestCase):
    async def test_libsql_engine_reachable(self):
        """
        Turso(libsql) 엔진이 비동기로 연결되는지 확인.
        로컬 sqlite로 실행 중이면 스킵한다.
        """
        if engine.url.drivername.startswith("sqlite"):
            self.skipTest("Local sqlite in use; libsql check skipped.")

        self.assertTrue(
            engine.url.drivername.startswith("libsql"),
            msg=f"Unexpected driver: {engine.url.drivername}",
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("select 1"))
            self.assertEqual(result.scalar(), 1)

    def test_chroma_uses_local_sqlite(self):
        """
        ChromaDB가 별도 로컬 디렉터리(sqlite backend)만 사용하는지 확인.
        """
        store = get_vector_store()
        chroma_path = Path(store.persist_directory)

        self.assertTrue(chroma_path.exists(), "Chroma directory does not exist")
        self.assertIn("chroma_db", str(chroma_path))
        # 메인 DB URL과 분리되어 있는지만 확인 (파일 이름 기준)
        self.assertNotIn("refresh_plus", str(chroma_path))


if __name__ == "__main__":
    unittest.main()
