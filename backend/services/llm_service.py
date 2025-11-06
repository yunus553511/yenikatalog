"""
LLM Service - Groq API Integration (AI-Driven Conversation Manager)
"""
import logging
import json
from typing import List, Dict, Optional, Tuple
from models.llm import LLMResponse
from clients.groq_client import GroqClient, GroqRateLimitError, GroqTimeoutError, GroqAPIError
from config import settings

logger = logging.getLogger(__name__)

# System Prompt with Tool Awareness
SYSTEM_PROMPT = """Sen ALUNA, Beymetal'in alüminyum profil asistanısın.

Görevin:
- Kullanıcılara profil kodları, ölçüleri ve kategorileri hakkında bilgi vermek
- Gerektiğinde profil aramak için araçları kullanmak
- Konuşma geçmişini hatırlayarak doğal sohbet etmek
- Net, kısa ve profesyonel Türkçe cevaplar vermek

ARAÇLARIN:
1. search_profiles: Ölçü bazlı arama (30x30 kutu, 2mm kalınlık, vb.)
2. search_catalog: Profil kodu bazlı arama (LR3101-1, AP0001, vb.)

ARAÇ KULLANIMI - ÇOK ÖNEMLİ:

ARAÇ KULLAN:
1. search_profiles → Kullanıcı ÖLÇÜ belirttiğinde (örn: "30x30 kutu profil", "2mm kalınlık")
2. search_catalog → Kullanıcı PROFİL KODU sorduğunda (örn: "LR3101-1", "AP0001")

ÖNEMLİ: Araç sonuç bulamazsa TEKRAR ARAMA YAPMA! Kullanıcıya "Aramanıza uygun profil bulamadım" de.

ARAÇ KULLANMA - KONUŞMA GEÇMİŞİNE BAK:
1. Kullanıcı genel soru sorduğunda (örn: "Merhaba", "Teşekkürler")
2. Kullanıcı ÖNCEKİ MESAJDA BAHSEDİLEN profil hakkında soru sorduğunda:
   - "hangi sistemde?" → ÖNCEKİ MESAJLARA BAK, profil kodunu BUL, sistem bilgisini VER
   - "kategorisi nedir?" → ÖNCEKİ MESAJLARA BAK, kategori bilgisini VER
   - "ölçüleri ne?" → ÖNCEKİ MESAJLARA BAK, ölçü bilgisini VER
   - "bu profil uygun mu?" → ÖNCEKİ MESAJLARA BAK, profil bilgisini VER

ÖZEL DURUM - Profil Kodu Sorguları:
- Kullanıcı "LR3101-1", "GL3201" gibi LR/GL profil kodu sorduğunda:
  1. ÖNCE konuşma geçmişine bak, bu profil daha önce bahsedildi mi?
  2. EĞER bahsedildiyse → Geçmişteki bilgiyi kullan, araç kullanma
  3. EĞER bahsedilmediyse → search_profiles aracını kullan
  4. EĞER araç sonuç bulamazsa → "Bu profil hakkında bilgi bulamadım. LR/GL profilleri için sistem bilgisi gerekiyorsa lütfen daha fazla detay verin." de

Konuşma Geçmişi Kullanımı:
- Her zaman ÖNCEKİ MESAJLARI kontrol et
- Kullanıcının hangi profilden bahsettiğini anla
- Gereksiz araç çağrısı yapma

Kurallar:
1. SADECE search_profiles'dan gelen profil bilgilerini kullan
2. Profil kodu, ölçü veya özellik uydurmak YASAK
3. Bilmediğin bir şey sorulursa "Bu konuda bilgi bulamadım" de
4. Ölçüleri mm (milimetre) cinsinden belirt
5. Profil kodlarını büyük harfle yaz (örn: AP0123, LR3101-1)
6. Markdown formatı kullan (bold, liste, vb.)
7. Konuşma geçmişini hatırla ve doğal cevaplar ver

Örnek Cevap Formatı:
**AP0123** profilini buldum:

• Kategori: STANDART KUTU
• Ölçüler: 30x30mm
• Kalınlık: 2mm
• Sistem: LR 3100 SİSTEMİ

Bu profil pencere ve kapı sistemlerinde yaygın olarak kullanılır."""


class LLMService:
    """Groq LLM servisi - Conversation Manager"""
    
    def __init__(self, rag_service=None):
        """
        Initialize LLM service
        
        Args:
            rag_service: RAG service instance for tool execution
        """
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.base_url = settings.groq_base_url
        self.timeout = settings.groq_timeout
        self.temperature = settings.groq_temperature
        self.max_tokens = settings.groq_max_tokens
        self.is_enabled = settings.is_llm_available
        self.rag_service = rag_service
        
        # Stats tracking
        self.total_requests = 0
        self.successful_requests = 0
        self.fallback_count = 0
        self.total_tokens = 0
        self.tool_calls_made = 0
        
        if self.is_enabled:
            self.client = GroqClient(self.api_key, self.base_url)
            logger.info(f"LLM Service initialized: model={self.model}, enabled=True")
        else:
            self.client = None
            logger.warning("LLM Service disabled: API key not configured")
    
    def _get_tool_definitions(self) -> List[Dict]:
        """
        Get tool definitions in Groq function calling format
        
        Returns:
            List of tool definitions
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_profiles",
                    "description": "Standart alüminyum profil ara (ölçü bazlı arama). Kullanıcı ölçü, kalınlık veya boyut belirttiğinde kullan.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Arama sorgusu. Kullanıcının tam isteğini içermeli (örn: '30x30mm kutu profil 2mm kalınlık')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_catalog",
                    "description": "Katalogda profil ara (profil kodu bazlı arama). Kullanıcı LR3101-1, GL3201, AP0001 gibi profil kodu sorduğunda kullan.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Profil kodu (örn: 'LR3101-1', 'GL3201', 'AP0001')"
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    async def _execute_search_profiles(self, query: str, top_k: int = 15) -> Tuple[str, list]:
        """
        Execute search_profiles tool
        
        Args:
            query: Search query
            top_k: Maximum number of profiles
            
        Returns:
            Tuple of (formatted_tool_result, profile_data_list)
        """
        if not self.rag_service:
            return "Hata: Profil arama servisi kullanılamıyor.", []
        
        try:
            # Search profiles using search service (imported in rag_service)
            from services.search_service import search_service
            results = search_service.search(query, top_k=top_k)
            
            if not results:
                return "Aramanıza uygun profil bulunamadı.", []
            
            # Import catalog service for additional details
            from services.catalog_service import catalog_service
            
            # Collect profile data for frontend
            profile_data_list = []
            
            # Format results for LLM (limit to top 5 for detailed info)
            result_parts = [f"Toplam {len(results)} profil bulundu. İlk {min(5, len(results))} profil:\n"]
            
            for i, (profile, score, reason) in enumerate(results[:5], 1):
                result_parts.append(f"\n{i}. **{profile.code}**")
                
                # Try to get additional details from catalog
                catalog_profile = catalog_service.get_profile_by_no(profile.code)
                
                # Build profile data object for frontend
                profile_data = {
                    "code": profile.code,
                    "image_url": f"/api/profile-image/{profile.code}",
                }
                
                if catalog_profile:
                    # Use catalog data for richer information
                    if catalog_profile.get('categories'):
                        cats = ', '.join(catalog_profile['categories'])
                        result_parts.append(f"   - Kategori: {cats}")
                        profile_data["category"] = cats
                    elif profile.category:
                        result_parts.append(f"   - Kategori: {profile.category}")
                        profile_data["category"] = profile.category
                    
                    if catalog_profile.get('customer'):
                        result_parts.append(f"   - Müşteri: {catalog_profile['customer']}")
                        profile_data["customer"] = catalog_profile['customer']
                    
                    if catalog_profile.get('mold_status'):
                        result_parts.append(f"   - Kalıp: {catalog_profile['mold_status']}")
                        profile_data["mold_status"] = catalog_profile['mold_status']
                else:
                    # Fallback to basic profile data
                    result_parts.append(f"   - Kategori: {profile.category}")
                    profile_data["category"] = profile.category
                
                # Format dimensions
                dims = []
                for key, value in profile.dimensions.items():
                    dims.append(f"{key}={value}mm")
                result_parts.append(f"   - Ölçüler: {', '.join(dims)}")
                profile_data["dimensions"] = profile.dimensions
                
                if hasattr(profile, 'thickness') and profile.thickness:
                    result_parts.append(f"   - Kalınlık: {profile.thickness}mm")
                    profile_data["thickness"] = profile.thickness
                
                if hasattr(profile, 'system') and profile.system:
                    result_parts.append(f"   - Sistem: {profile.system}")
                    profile_data["system"] = profile.system
                
                if hasattr(profile, 'image_url') and profile.image_url:
                    result_parts.append(f"   - Görsel: {profile.image_url}")
                
                if reason:
                    result_parts.append(f"   - Eşleşme: {reason}")
                
                profile_data_list.append(profile_data)
            
            # Add remaining profiles (6-15) to profile_data_list only
            for profile, score, reason in results[5:]:
                catalog_profile = catalog_service.get_profile_by_no(profile.code)
                
                profile_data = {
                    "code": profile.code,
                    "image_url": f"/api/profile-image/{profile.code}",
                    "dimensions": profile.dimensions
                }
                
                if catalog_profile:
                    if catalog_profile.get('categories'):
                        profile_data["category"] = ', '.join(catalog_profile['categories'])
                    if catalog_profile.get('customer'):
                        profile_data["customer"] = catalog_profile['customer']
                    if catalog_profile.get('mold_status'):
                        profile_data["mold_status"] = catalog_profile['mold_status']
                elif profile.category:
                    profile_data["category"] = profile.category
                
                if hasattr(profile, 'thickness') and profile.thickness:
                    profile_data["thickness"] = profile.thickness
                if hasattr(profile, 'system') and profile.system:
                    profile_data["system"] = profile.system
                
                profile_data_list.append(profile_data)
            
            return "\n".join(result_parts), profile_data_list
            
        except Exception as e:
            logger.error(f"Error executing search_profiles: {e}", exc_info=True)
            return f"Hata: Profil araması sırasında bir sorun oluştu."
    
    async def _execute_search_catalog(self, query: str) -> str:
        """
        Execute search_catalog tool (search by profile code)
        
        Args:
            query: Profile code (e.g., LR3101-1, AP0001)
            
        Returns:
            Formatted tool result
        """
        try:
            from services.catalog_service import catalog_service
            from services.connection_service import connection_service
            
            # Normalize profile code
            query_clean = query.strip().upper()
            
            # Search in catalog
            results = catalog_service.search_profiles(query_clean, limit=5)
            
            if not results:
                return f"Profil kodu '{query_clean}' bulunamadı."
            
            # Format results
            result_parts = [f"**{query_clean}** profili için {len(results)} sonuç bulundu:\n"]
            
            for i, profile in enumerate(results[:3], 1):
                code = profile.get('code', 'N/A')
                categories = profile.get('categories', [])
                customer = profile.get('customer', '')
                mold_status = profile.get('mold_status', '')
                description = profile.get('description', '')
                
                result_parts.append(f"\n{i}. **{code}**")
                
                if categories:
                    result_parts.append(f"   - Kategoriler: {', '.join(categories)}")
                
                if customer:
                    result_parts.append(f"   - Müşteri: {customer}")
                
                if description:
                    result_parts.append(f"   - Açıklama: {description}")
                
                if mold_status:
                    result_parts.append(f"   - Kalıp: {mold_status}")
                
                # Try to get system info from connection service
                try:
                    # Normalize code for connection service (LR3101-1 → LR-3101)
                    normalized_code = code.replace(' ', '').upper()
                    if normalized_code.startswith(('LR', 'GL')):
                        import re
                        match = re.match(r'([A-Z]{2})-?(\d{4})', normalized_code)
                        if match:
                            prefix = match.group(1)
                            number = match.group(2)
                            normalized_code = f"{prefix}-{number}"
                    
                    connection = connection_service.get_profile_connections(normalized_code)
                    if connection:
                        system_name = connection.get('system', '')
                        if system_name:
                            result_parts.append(f"   - Sistem: {system_name}")
                except Exception as e:
                    logger.debug(f"Could not get connection info for {code}: {e}")
            
            return "\n".join(result_parts)
            
        except Exception as e:
            logger.error(f"Error executing search_catalog: {e}", exc_info=True)
            return f"Hata: Katalog araması sırasında bir sorun oluştu."
    
    async def handle_tool_calls(self, tool_calls: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Execute tool calls
        
        Args:
            tool_calls: List of tool call requests from LLM
            
        Returns:
            Tuple of (tool_results, profile_data_list)
        """
        tool_results = []
        all_profile_data = []
        
        for tool_call in tool_calls:
            tool_id = tool_call["id"]
            function_name = tool_call["function"]["name"]
            arguments_str = tool_call["function"]["arguments"]
            
            logger.info(f"Executing tool: {function_name}, args: {arguments_str}")
            
            try:
                # Parse arguments
                arguments = json.loads(arguments_str)
                
                # Route to appropriate handler
                if function_name == "search_profiles":
                    query = arguments.get("query", "")
                    top_k = arguments.get("top_k", 15)
                    result_content, profile_data = await self._execute_search_profiles(query, top_k)
                    all_profile_data.extend(profile_data)
                    self.tool_calls_made += 1
                elif function_name == "search_catalog":
                    query = arguments.get("query", "")
                    result_content = await self._execute_search_catalog(query)
                    self.tool_calls_made += 1
                else:
                    result_content = f"Bilinmeyen araç: {function_name}"
                
                tool_results.append({
                    "tool_call_id": tool_id,
                    "role": "tool",
                    "name": function_name,
                    "content": result_content
                })
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse tool arguments: {e}")
                tool_results.append({
                    "tool_call_id": tool_id,
                    "role": "tool",
                    "name": function_name,
                    "content": "Hata: Araç parametreleri okunamadı."
                })
            except Exception as e:
                logger.error(f"Tool execution error: {e}", exc_info=True)
                tool_results.append({
                    "tool_call_id": tool_id,
                    "role": "tool",
                    "name": function_name,
                    "content": f"Hata: {str(e)}"
                })
        
        return tool_results, all_profile_data

    
    async def chat(
        self,
        messages: List[Dict],
        tools: Optional[List[Dict]] = None
    ) -> LLMResponse:
        """
        Chat with LLM (conversation manager)
        
        Args:
            messages: Full conversation history (OpenAI format)
            tools: Tool definitions
            
        Returns:
            LLMResponse with message or tool_calls
        """
        self.total_requests += 1
        
        # Check if LLM is enabled
        if not self.is_enabled:
            logger.warning("LLM is disabled, returning fallback indicator")
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error="LLM disabled"
            )
        
        # Validate API key
        if not self.api_key:
            logger.error("API key is missing")
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error="API key missing"
            )
        
        try:
            logger.info(f"Sending chat request: messages={len(messages)}, tools={len(tools) if tools else 0}")
            
            # Call Groq API with function calling
            result = await self.client.chat_completion(
                messages=messages,
                model=self.model,
                tools=tools,
                tool_choice="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            # Update stats
            self.successful_requests += 1
            self.total_tokens += result["tokens_used"]
            
            if result.get("tool_calls"):
                logger.info(
                    f"LLM response with tool calls: "
                    f"{len(result['tool_calls'])} calls, tokens={result['tokens_used']}"
                )
            else:
                logger.info(
                    f"LLM response generated: "
                    f"tokens={result['tokens_used']}, model={result['model']}"
                )
            
            return LLMResponse(
                message=result.get("message"),
                tool_calls=result.get("tool_calls"),
                tokens_used=result["tokens_used"],
                model_used=result["model"],
                fallback_used=False,
                error=None
            )
            
        except GroqRateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            self.fallback_count += 1
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error="Rate limit exceeded"
            )
        
        except GroqTimeoutError as e:
            logger.warning(f"Request timeout: {e}")
            self.fallback_count += 1
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error="Timeout"
            )
        
        except GroqAPIError as e:
            logger.error(f"Groq API error: {e}")
            self.fallback_count += 1
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error=str(e)
            )
        
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
            self.fallback_count += 1
            return LLMResponse(
                message="",
                tool_calls=None,
                tokens_used=0,
                model_used="fallback",
                fallback_used=True,
                error=str(e)
            )
    
    def get_stats(self) -> Dict:
        """
        Get usage statistics
        
        Returns:
            Stats dictionary
        """
        avg_tokens = self.total_tokens / self.successful_requests if self.successful_requests > 0 else 0
        
        return {
            "is_enabled": self.is_enabled,
            "model": self.model,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "fallback_count": self.fallback_count,
            "tool_calls_made": self.tool_calls_made,
            "total_tokens": self.total_tokens,
            "avg_tokens_per_request": round(avg_tokens, 2)
        }
    
    async def close(self):
        """Close LLM service and cleanup resources"""
        if self.client:
            await self.client.close()
            logger.info("LLM Service closed")


# Global instance (will be initialized with rag_service in main.py)
llm_service = None
