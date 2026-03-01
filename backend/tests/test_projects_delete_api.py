from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from backend.dependencies import get_db
from backend.models import PipelineJob, PipelineJobEvent, Project, User
from backend.routers import projects


def _build_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(projects.router)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app), TestingSessionLocal


def test_delete_project_also_deletes_linked_pipeline_jobs():
    client, SessionLocal = _build_client()

    with SessionLocal() as db:
        user = User(id=1, email="user@example.com")
        db.add(user)
        db.flush()

        project = Project(user_id=user.id, name="Delete Me")
        db.add(project)
        db.flush()

        job = PipelineJob(
            job_id="job-delete-1",
            project_id=project.id,
            job_type="vector",
            status="queued",
            step=0,
            message="Queued",
        )
        db.add(job)
        db.flush()

        db.add(
            PipelineJobEvent(
                job_id=job.job_id,
                status=job.status,
                step=job.step,
                message=job.message,
            )
        )
        db.commit()
        project_id = project.id

    response = client.delete(f"/api/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

    with SessionLocal() as db:
        assert db.query(Project).filter(Project.id == project_id).first() is None
        assert db.query(PipelineJob).filter(PipelineJob.project_id == project_id).count() == 0
        assert db.query(PipelineJobEvent).filter(PipelineJobEvent.job_id == "job-delete-1").count() == 0
