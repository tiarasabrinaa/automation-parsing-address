from datetime import datetime

from pymongo.errors import DuplicateKeyError

from app.core.database import get_database
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.auth import (
    AuthResponse,
    AuthToken,
    PasswordChangeRequest,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
    UserUpdateRequest,
)
from app.utils.mongo import serialize_document, to_object_id


class AuthService:
    def __init__(self) -> None:
        pass

    @property
    def collection(self):
        return get_database().users

    async def register(self, payload: UserRegisterRequest) -> AuthResponse:
        email = payload.email.lower()
        username = payload.username.strip().lower()

        if await self.collection.find_one({"email": email}):
            raise ValueError("Email already registered")
        if await self.collection.find_one({"username": username}):
            raise ValueError("Username already taken")

        now = datetime.utcnow()
        document = {
            "email": email,
            "username": username,
            "full_name": payload.full_name.strip(),
            "password_hash": hash_password(payload.password),
            "role": "user",
            "is_active": True,
            "last_login_at": None,
            "created_at": now,
            "updated_at": now,
        }

        try:
            result = await self.collection.insert_one(document)
        except DuplicateKeyError as exc:
            raise ValueError("User already exists") from exc

        user = await self.get_user_by_id(str(result.inserted_id))
        return AuthResponse(user=user, token=self._build_token(user))

    async def login(self, payload: UserLoginRequest) -> AuthResponse:
        email = payload.email.lower()
        document = await self.collection.find_one({"email": email})
        if document is None:
            raise ValueError("Invalid email or password")

        if not verify_password(payload.password, document["password_hash"]):
            raise ValueError("Invalid email or password")

        await self.collection.update_one(
            {"_id": document["_id"]},
            {"$set": {"last_login_at": datetime.utcnow(), "updated_at": datetime.utcnow()}},
        )

        user = await self.get_user_by_id(str(document["_id"]))
        return AuthResponse(user=user, token=self._build_token(user))

    async def get_user_by_id(self, user_id: str) -> UserPublic:
        document = await self.collection.find_one({"_id": to_object_id(user_id)})
        if document is None:
            raise ValueError("User not found")
        return self._to_public(document)

    async def update_profile(self, user_id: str, payload: UserUpdateRequest) -> UserPublic:
        document = await self.collection.find_one({"_id": to_object_id(user_id)})
        if document is None:
            raise ValueError("User not found")

        update_data = payload.model_dump(exclude_unset=True)
        if "username" in update_data:
            update_data["username"] = update_data["username"].strip().lower()
            existing = await self.collection.find_one(
                {"username": update_data["username"], "_id": {"$ne": document["_id"]}}
            )
            if existing is not None:
                raise ValueError("Username already taken")
        if "full_name" in update_data:
            update_data["full_name"] = update_data["full_name"].strip()

        update_data["updated_at"] = datetime.utcnow()
        await self.collection.update_one({"_id": document["_id"]}, {"$set": update_data})
        return await self.get_user_by_id(user_id)

    async def change_password(self, user_id: str, payload: PasswordChangeRequest) -> None:
        document = await self.collection.find_one({"_id": to_object_id(user_id)})
        if document is None:
            raise ValueError("User not found")

        if not verify_password(payload.current_password, document["password_hash"]):
            raise ValueError("Current password is invalid")

        await self.collection.update_one(
            {"_id": document["_id"]},
            {
                "$set": {
                    "password_hash": hash_password(payload.new_password),
                    "updated_at": datetime.utcnow(),
                }
            },
        )

    @staticmethod
    def _to_public(document: dict) -> UserPublic:
        data = serialize_document(document)
        if data is None:
            raise ValueError("User document is empty")
        return UserPublic.model_validate(data)

    @staticmethod
    def _build_token(user: UserPublic) -> AuthToken:
        access_token = create_access_token(
            user.id,
            extra_claims={"email": str(user.email), "username": user.username, "role": user.role},
        )
        return AuthToken(access_token=access_token)
