from services.basic_service import ParserClass
from schema import ParserSource, ProductSchema
from logger import get_logger
from config import Config

import aiohttp
import asyncio
import uuid
import re

from logging import Logger
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from datetime import datetime

config: Config = Config()

class EbayService(ParserClass):
    def __init__(self):
        super().__init__()
        self.products: List[ProductSchema] = []
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
        self.base_url: str = config.EBAY_URL
        self.logger: Logger = get_logger("ebay-service")
    
    async def _async_request(self, prompt: str, timeout: int = 10) -> Optional[str]:
        REQUEST_URL: str = f"{self.base_url}{prompt}"
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(REQUEST_URL, headers=self.headers) as response:
                    if response.status == 200:
                        self.logger.info(f"Connected to - {REQUEST_URL}")
                        return await response.text()
                    else:
                        self.logger.error(f"Request failed with status {response.status} - {REQUEST_URL}")
                        return None
        except asyncio.TimeoutError:
            self.logger.error(f"Request timed out - {REQUEST_URL}")
            return None
        except Exception as e:
            self.logger.error(f"Cannot connect to source - {REQUEST_URL}: {str(e)}")
            return None
    
    def _parse_price(self, price_text: str) -> float:
        try:
            cleaned = re.sub(r'[^\d.]', '', price_text)
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0
    
    def _parse_rating(self, rating_html) -> Optional[float]:
        try:
            stars = rating_html.find_all('svg', class_='icon--16')
            filled_stars = len([s for s in stars if 'star-filled' in str(s)])
            return float(filled_stars) if filled_stars > 0 else None
        except:
            return None
    
    def _parse_product_card(self, card_html: BeautifulSoup) -> Optional[ProductSchema]:
        try:
            link_elem = card_html.find('a', class_='s-card__link')
            product_url = link_elem['href'] if link_elem else ""
            
            if not product_url:
                return None
            
            title_elem = card_html.find('span', class_='su-styled-text primary default')
            product_title = title_elem.text.strip() if title_elem else ""
            
            price_elem = card_html.find('span', class_='su-styled-text primary bold large-1 s-card__price')
            product_price = self._parse_price(price_elem.text) if price_elem else 0.0
            
            rating_container = card_html.find('div', class_='x-star-rating')
            product_rating = self._parse_rating(rating_container) if rating_container else None
            
            img_elem = card_html.find('img', class_='s-card__image')
            product_image = img_elem['src'] if img_elem and img_elem.get('src') else None
            
            reviews_elem = card_html.find('span', class_='s-card__reviews-count')
            product_views = None
            if reviews_elem:
                reviews_text = reviews_elem.text
                match = re.search(r'(\d+)', reviews_text)
                product_views = int(match.group(1)) if match else None
            
            return ProductSchema(
                product_id=str(uuid.uuid4()),
                parsed_source=ParserSource.EBAY,
                product_title=product_title,
                product_price=product_price,
                product_rating=product_rating,
                product_sold_out=None,
                product_views=product_views,
                product_image=product_image,
                product_url=product_url,
                product_parsed_date=datetime.now()
            )
        
        except Exception as e:
            self.logger.error(f"Error parsing product card: {str(e)}")
            return None
    
    async def parse(self, product_name: str) -> List[ProductSchema]:
        try:
            search_query = product_name.replace(' ', '+')
            html_content = await self._async_request(f"sch/i.html?_nkw={search_query}")
            
            if not html_content:
                self.logger.error("Failed to get response from eBay")
                return []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            product_cards = soup.find_all('div', class_='su-card-container')
            
            self.logger.info(f"Found {len(product_cards)} products for '{product_name}'")
            
            self.products = []
            for card in product_cards:
                product = self._parse_product_card(card)
                if product:
                    self.products.append(product)
            
            self.logger.info(f"Successfully parsed {len(self.products)} products")
            return self.products
        
        except Exception as e:
            self.logger.error(f"Error in parse method: {str(e)}")
            return []
    
    async def parse_multiple(self, product_names: List[str]) -> Dict[str, List[ProductSchema]]:
        tasks = [self.parse(name) for name in product_names]
        results = await asyncio.gather(*tasks)
        return {name: result for name, result in zip(product_names, results)}
    
    def get_products(self) -> List[ProductSchema]:
        return self.products
