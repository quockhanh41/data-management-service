# import os
# import sys
# import asyncio

# # Thêm thư mục gốc vào Python path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(os.path.dirname(current_dir))
# sys.path.append(root_dir)

# from app.services.redis_service import RedisService

# async def main():
#     redis_service = RedisService()
#     await redis_service.start_update_loop()

# if __name__ == "__main__":
#     asyncio.run(main()) 