import asyncio
import motor.motor_asyncio
import servicios.credenciales as credenciales

def conexion_mongo(db = 'report'):
    MONGO_DETAILS = f"mongodb://{credenciales.mongo()['usuario']}:{credenciales.mongo()['password']}@{credenciales.mongo()['servidor']}"
    client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
    return client[db]
