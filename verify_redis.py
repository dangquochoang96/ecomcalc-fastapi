from app.utils.redis import get_redis_client
import sys


def test_redis_connection():
    try:
        client = get_redis_client()
        client.ping()
        print("Redis connection successful")

        # Also clean up any test keys if we were to set any
    except Exception as e:
        print(f"Redis connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_redis_connection()
