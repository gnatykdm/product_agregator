from config import Config
from logger import get_logger
from schema import ProductSchema, ParserSource
from services.basic_service import ParserClass

import asyncio
import aiohttp
import random
import uuid

from bs4 import BeautifulSoup
from logging import Logger
from typing import List, Dict, Optional
from datetime import datetime

config: Config = Config()

class AmazonService(ParserClass):
    def __init__(self):
        super().__init__()
        self.base_url: str = config.AMAZON_URL
        self.headers: Dict[str, str] = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "DNT": "1"
        }
        self.logger: Logger = get_logger("amazon-service")
        self.products: List[ProductSchema] = []
        self.proxy: Optional[str] = None
    
    def set_proxy(self, proxy: str):
        self.proxy = proxy
        self.logger.info(f"Proxy set: {proxy}")
    
    def _save_html_debug(self, html_content: str, filename: str = "amazon_debug.html"):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            self.logger.info(f"HTML content saved to {filename} for debugging")
        except Exception as e:
            self.logger.error(f"Failed to save debug HTML: {e}")
    
    async def _async_request(self, product_name: str, timeout: int = 10) -> Optional[str]:
        if not product_name:
            self.logger.error("Input product_name can't be empty")
            return None
        
        await asyncio.sleep(random.uniform(1, 3))
        
        url = f"{self.base_url}{product_name.replace(' ', '+')}"
        
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            connector = aiohttp.TCPConnector()
            
            async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
                request_kwargs = {
                    "url": url,
                    "headers": self.headers,
                    "allow_redirects": True
                }
                
                if self.proxy:
                    request_kwargs["proxy"] = self.proxy
                
                async with session.get(**request_kwargs) as response:
                    if response.status == 200:
                        self.logger.info(f"Successfully connected to - {url}")
                        return await response.text()
                    elif response.status == 503:
                        self.logger.error("Amazon blocked the request (503). Try using a proxy or reducing request frequency.")
                        return None
                    else:
                        self.logger.error(f"Received status code {response.status} from {url}")
                        return None
        
        except asyncio.TimeoutError:
            self.logger.error(f"Request timed out for {url}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to {url}: {e}")
            return None
    
    def _parse_product_box(self, box: BeautifulSoup) -> Optional[ProductSchema]:
        try:
            asin = box.get("data-asin")
            if not asin:
                return None
            
            title = "No title"
            title_selectors = [
                "h2.a-size-medium span",
                "h2 span.a-text-normal",
                "h2 a span"
            ]
            for selector in title_selectors:
                title_tag = box.select_one(selector)
                if title_tag:
                    title = title_tag.text.strip()
                    break
            
            product_url = None
            url_selectors = [
                "h2 a.a-link-normal",
                "a.a-link-normal.s-no-outline",
                "a.a-link-normal.s-line-clamp-2"
            ]
            
            for selector in url_selectors:
                url_tag = box.select_one(selector)
                if url_tag and url_tag.get('href'):
                    href = url_tag['href']
                    if href.startswith('/'):
                        product_url = f"https://www.amazon.com{href}"
                    elif href.startswith('http'):
                        product_url = href
                    break
            
            if not product_url:
                product_url = f"https://www.amazon.com/dp/{asin}"
            
            price = 0.0
            price_whole_tag = box.select_one("span.a-price-whole")
            price_fraction_tag = box.select_one("span.a-price-fraction")
            
            if price_whole_tag and price_fraction_tag:
                try:
                    whole = price_whole_tag.text.replace(',', '').replace('.', '').strip()
                    fraction = price_fraction_tag.text.strip()
                    price = float(f"{whole}.{fraction}")
                except ValueError:
                    self.logger.warning(f"Could not parse price for ASIN {asin}")
            
            rating = None
            rating_tag = box.select_one("span.a-icon-alt")
            if rating_tag:
                try:
                    rating_text = rating_tag.text.strip()
                    rating = float(rating_text.split()[0])
                except (ValueError, IndexError):
                    self.logger.warning(f"Could not parse rating for ASIN {asin}")
            
            sold_count = None
            bought_tag = box.select_one("span.a-size-base.a-color-secondary")
            if bought_tag and "bought" in bought_tag.text.lower():
                try:
                    text = bought_tag.text.strip()
                    if "K+" in text or "k+" in text:
                        num = text.split("K")[0].replace("+", "").strip()
                        sold_count = int(float(num) * 1000)
                except (ValueError, IndexError):
                    self.logger.warning(f"Could not parse sold count for ASIN {asin}")
            
            img_url = None
            img_tag = box.select_one("img.s-image")
            if img_tag:
                img_url = img_tag.get("src") or img_tag.get("data-image-source")
            
            return ProductSchema(
                product_id=str(uuid.uuid4()),
                parsed_source=ParserSource.AMAZON,
                product_title=title,
                product_price=price,
                product_rating=rating,
                product_sold_out=sold_count,
                product_views=None,
                product_image=img_url,
                product_url=product_url,
                product_parsed_date=datetime.now()
            )
        
        except Exception as e:
            self.logger.warning(f"Error parsing product box for ASIN {asin if 'asin' in locals() else 'unknown'}: {e}")
            return None
    
    async def parse(self, product_name: str, debug: bool = False) -> List[ProductSchema]:
        html_content = await self._async_request(product_name)
        
        if not html_content:
            return []
        
        if debug:
            self._save_html_debug(html_content)
        
        soup = BeautifulSoup(html_content, 'html.parser')
        product_boxes = soup.find_all("div", {"data-component-type": "s-search-result"})
        
        if not product_boxes:
            self.logger.warning(f"No products found for search term: {product_name}")
            return []
        
        self.products = []
        for box in product_boxes:
            product = self._parse_product_box(box)
            if product:
                self.products.append(product)
        
        self.logger.info(f"Successfully parsed {len(self.products)} products for search term: {product_name}")
        return self.products
    
    async def parse_multiple(self, product_names: List[str], debug: bool = False) -> Dict[str, List[ProductSchema]]:
        tasks = [self.parse(name, debug) for name in product_names]
        results = await asyncio.gather(*tasks)
        return {name: result for name, result in zip(product_names, results)}
    
    def get_products(self) -> List[ProductSchema]:
        return self.products
