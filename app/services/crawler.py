import wikipediaapi
from typing import List, Dict
import logging
import os
from dotenv import load_dotenv
import requests
load_dotenv()

logger = logging.getLogger(__name__)

class Crawler:
    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            # user_agent=os.getenv('WIKIPEDIA_API_USER_AGENT'),
            language='en'  # Default language, will be changed in crawl_wikipedia
        )

    async def crawl_wikipedia(self, topic: str, language: str) -> str:
        try:
            # Create a new Wikipedia instance with the specified language
            wiki = wikipediaapi.Wikipedia(
                # user_agent=os.getenv('WIKIPEDIA_API_USER_AGENT'),
                language=language
            )
            
            # Get the page
            page = wiki.page(topic)
            
            if page.exists():
                return page.text
            else:
                logger.warning(f"Wikipedia page not found for topic: {topic}")
                return ""
        except Exception as e:
            logger.error(f"Error crawling Wikipedia: {str(e)}")
            return ""

    async def crawl_nature(self, topic: str, language: str) -> str:
        # Implement Nature crawling logic
        try:
            # Implement Nature crawling logic
            api_key = os.getenv('NATURE_API_KEY')
            api_url = os.getenv('NATURE_API_URL')

            # Tạo truy vấn tìm kiếm 
            query = f"q={topic}&api_key={api_key}&p=10"  # Lấy tối đa 10 kết quả

            # Gửi yêu cầu GET đến API
            response = requests.get(f"{api_url}/search", params=query)
            response.raise_for_status()  # Ném ra lỗi nếu trả về không thành công

            # Xử lý dữ liệu trả về
            data = response.json()
            print(data)

            return ""
        except Exception as e:
            logger.error(f"Error crawling Nature: {str(e)}")
            return ""

    async def crawl_pubmed(self, topic: str) -> str:
        # Implement PubMed crawling logic
        return ""

    async def crawl(self, topic: str, sources: List[str], language: str) -> Dict[str, str]:
        results = {}
        for source in sources:
            if source == "wikipedia":
                results[source] = await self.crawl_wikipedia(topic, language)
            elif source == "nature":
                results[source] = await self.crawl_nature(topic)
            elif source == "pubmed":
                results[source] = await self.crawl_pubmed(topic)
        return results

    async def close(self):
        # No need to close anything for wikipedia-api
        pass 

# # test wikipedia
# if __name__ == "__main__":
#     import asyncio
    
#     async def main():
#         crawler = Crawler()
#         result = await crawler.crawl_wikipedia("AI", "en")
#         print(result)
#         await crawler.close()
    
#     asyncio.run(main())
