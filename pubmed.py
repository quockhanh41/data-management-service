import requests
import xml.etree.ElementTree as ET
import time

def crawl_pubmed(topic, language="eng"):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi"
    fetch_url = f"{base_url}efetch.fcgi"
    
    # Tạo truy vấn tìm kiếm
    query = f"{topic}[All Fields]+AND+{language}[Language]"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 3,  # Lấy tối đa 10 bài
        "retmode": "xml"
    }
    
    try:
        # Bước 1: Tìm kiếm ID bài báo
        search_response = requests.get(search_url, params=params)
        search_response.raise_for_status()
        
        search_tree = ET.fromstring(search_response.content)
        id_list = [id_elem.text for id_elem in search_tree.findall(".//Id")]
        
        if not id_list:
            print(f"No articles found for topic '{topic}' in language '{language}'")
            return
        
        # Bước 2: Lấy chi tiết bài báo
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(id_list),
            "retmode": "xml"
        }
        fetch_response = requests.get(fetch_url, params=fetch_params)
        fetch_response.raise_for_status()
        
        fetch_tree = ET.fromstring(fetch_response.content)
        print(f"Found {len(id_list)} articles for topic '{topic}' in language '{language}':")
        
        for article in fetch_tree.findall(".//Article"):
            title_elem = article.find(".//ArticleTitle")
            abstract_elem = article.find(".//AbstractText")
            
            title = title_elem.text if title_elem is not None else "N/A"
            
            abstract = abstract_elem.text if abstract_elem is not None else "No abstract available"
            
            print(f"\nTitle: {title}")
            print(f"Abstract: {abstract[:200]}...")  # Giới hạn độ dài tóm tắt
            # write abstract to file, file name is {{title}}.txt
            with open(f"{title}.txt", "w") as f:
                f.write(abstract)
        

        # Tôn trọng giới hạn tốc độ của NCBI
        time.sleep(0.34)  # 3 yêu cầu/giây
        
    except requests.exceptions.RequestException as e:
        print(f"Error crawling PubMed: {e}")
    except ET.ParseError:
        print("Error parsing XML response")

# Ví dụ sử dụng
topic = "AI"
language = "eng"  # eng cho tiếng Anh
crawl_pubmed(topic, language)