import requests
import json
import os

def crawl_nature(topic, language="en"):
    # Thay YOUR_API_KEY bằng API key của bạn
    api_key = "6e7487e992afd67e6f3724db314b1ac0"
    base_url = "https://api.springernature.com/meta/v2/json"
    max_results = 3  # Số lượng kết quả tối đa cần thu thập
    page_size = 10  # Số lượng kết quả mỗi lần truy vấn
    start = 1  # Vị trí bắt đầu của truy vấn
    collected_articles = []  # Danh sách các bài viết đã thu thập

    try:
        while len(collected_articles) < max_results:
            # Tạo truy vấn tìm kiếm với phân trang
            query = f'q={topic.replace(" ", "+")}&api_key={api_key}&p={page_size}&s={start}'
            response = requests.get(f"{base_url}?{query}")
            response.raise_for_status()  # Kiểm tra lỗi HTTP
            
            data = response.json()
            articles = data.get("records", [])
            
            if not articles:
                print(f"No more articles found for topic '{topic}'.")
                break
            
            for article in articles:
                title = article.get("title", "").lower()
                # Check if the exact keyword or phrase is in the title
                if topic.lower() not in title.split():
                    continue  # Skip if the exact keyword or phrase is not in the title
                
                collected_articles.append(article)
                if len(collected_articles) >= max_results:
                    break
            
            # Tăng vị trí bắt đầu để lấy trang tiếp theo
            start += page_size
        
        if not collected_articles:
            print(f"No articles found for topic '{topic}'.")
            return
        
        print(f"Found {len(collected_articles)} articles for topic '{topic}':")
        
        # Tạo thư mục để lưu kết quả
        output_dir = "nature_results"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for article in collected_articles:
            title = article.get("title", "").lower()
            abstract = article.get("abstract", "No abstract available")
            doi = article.get("doi", "N/A")
            
            print(f"\nTitle: {title}")
            print(f"DOI: {doi}")
            print(f"Abstract: {abstract[:200]}...")  # Giới hạn độ dài tóm tắt
            
            # Tạo tên file an toàn
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title[:50]  # Giới hạn độ dài tên file
            file_path = os.path.join(output_dir, f"{safe_title}.txt")
            
            # Ghi file với encoding UTF-8
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"Title: {title}\n")
                f.write(f"DOI: {doi}\n")
                f.write(f"Abstract: {abstract}\n")
                
            print(f"Saved to: {file_path}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("Unauthorized: Please check your API key.")
        else:
            print(f"Error crawling Nature: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error crawling Nature: {e}")

# Ví dụ sử dụng
if __name__ == "__main__":
    topic = "AI"
    language = "en"
    crawl_nature(topic, language)