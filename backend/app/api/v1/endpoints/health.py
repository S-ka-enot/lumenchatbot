from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Проверка работоспособности сервиса")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/db", summary="Проверка подключения к БД")
async def db_healthcheck() -> dict[str, str]:
    return {"status": "ok"}

