I want to integrate our parsing app and open-webui

You should refer this repo.
https://github.com/open-webui/open-webui

and refer this analysis
# DeepWiki Q&A with Code Context for Repository: open-webui/open-webui
## Q1
지식기반을 생성할때 parser를 호출하는 코드부분을 알고 싶어 parser에 문서를 보내고 결과물을 받는 전체 과정이 궁금해
### Answer
## 지식 기반 생성 시 파서 호출 과정 요약

지식 기반 생성 시 문서를 파서로 보내고 결과를 받는 과정은 크게 (1) 파일 추가 API 진입 → (2) `process_file` 호출 → (3) 로더(파서) 실행 → (4) 결과를 `Document` 객체로 변환 → (5) 벡터 DB 저장 순서로 이루어집니다. 대표적으로 `MistralLoader`를 사용한 OCR 파서 흐름을 중심으로 설명합니다.

---

## 전체 흐름 상세

### 1. 지식 기반에 파일 추가 (API 진입점)
- `add_file_to_knowledge_by_id` 엔드포인트가 파일 ID와 컬렉션(지식 기반) ID를 받아 `process_file`을 호출합니다 open-webui:653-703 .

### 2. process_file 호출 (파서 선택 및 실행)
- `process_file` 함수 내부에서 파일 형식에 맞는 로더를 선택하여 실행합니다. 이 함수는 `retrieval/loaders` 아래의 로더들을 사용하며, 예를 들어 PDF/이미지의 경우 `MistralLoader`가 사용될 수 있습니다.
- `process_file`은 비동기로 실행될 수 있으며, 배치 처리도 지원합니다(`process_files_batch`) open-webui:1056-1067 .

### 3. 파서(로더) 실행 예시: MistralLoader
- `MistralLoader`는 `_get_session`으로 HTTP 세션을 만들고 외부 OCR API를 호출한 뒤, `_process_results`에서 응답을 `Document` 객체 리스트로 변환합니다 open-webui:486-514 open-webui:515-591 .
- 각 `Document`는 `page_content`와 `metadata`(페이지 번호, 파일명 등)를 포함합니다.

### 4. Document 객체 벡터화 및 저장
- 생성된 `Document` 리스트는 임베딩 함수를 통해 벡터로 변환되고 지정된 컬렉션(벡터 DB)에 저장됩니다. 이 과정은 `process_file` 내부 또는 `embed_knowledge_base_metadata` 등에서 이루어집니다 open-webui:500-505 .

### 5. 검색 및 활용
- 저장된 문서는 `query_knowledge_files` 같은 툴이나 RAG 검색 시 벡터 검색을 통해 조회되어 사용자에게 반환됩니다 open-webui:1611-1654 open-webui:1752-1781 .

---

## 관련 코드 위치
- **API 엔드포인트**: `backend/open_webui/routers/knowledge.py` (`add_file_to_knowledge_by_id`, `process_file`)
- **파서(로더) 예시**: `backend/open_webui/retrieval/loaders/mistral.py` (`MistralLoader`)
- **검색/활용**: `backend/open_webui/tools/builtin.py` (`query_knowledge_files`)

---

## Notes
- 위 흐름은 파일 종류에 따라 다른 로더(`TikaLoader`, `DoclingLoader`, `MarkerLoader` 등)로 대체될 수 있습니다.
- 웹 페이지 추가 시 `SafeWebBaseLoader`가 사용되며, 이는 HTML을 파싱하여 `Document`를 생성합니다 open-webui:551-633 .
- 전체 파이프라인은 비동기 처리와 배치 처리를 지원하여 대용량 파일도 처리할 수 있습니다.

Wiki pages you might want to explore:
- [Overview (open-webui/open-webui)](/wiki/open-webui/open-webui#1)
### Citations
**File:** backend/open_webui/routers/knowledge.py (L500-505)
```python
        await embed_knowledge_base_metadata(
            request,
            knowledge.id,
            knowledge.name,
            knowledge.description,
        )
```
**File:** backend/open_webui/routers/knowledge.py (L653-703)
```python
@router.post("/{id}/file/add", response_model=Optional[KnowledgeFilesResponse])
def add_file_to_knowledge_by_id(
    request: Request,
    id: str,
    form_data: KnowledgeFileIdForm,
    user=Depends(get_verified_user),
    db: Session = Depends(get_session),
):
    knowledge = Knowledges.get_knowledge_by_id(id=id, db=db)
    if not knowledge:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )

    if (
        knowledge.user_id != user.id
        and not AccessGrants.has_access(
            user_id=user.id,
            resource_type="knowledge",
            resource_id=knowledge.id,
            permission="write",
            db=db,
        )
        and user.role != "admin"
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    file = Files.get_file_by_id(form_data.file_id, db=db)
    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.NOT_FOUND,
        )
    if not file.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.FILE_NOT_PROCESSED,
        )

    # Add content to the vector database
    try:
        process_file(
            request,
            ProcessFileForm(file_id=form_data.file_id, collection_name=id),
            user=user,
            db=db,
        )
```
**File:** backend/open_webui/routers/knowledge.py (L1056-1067)
```python
    try:
        result = await process_files_batch(
            request=request,
            form_data=BatchProcessFilesForm(files=files, collection_name=id),
            user=user,
            db=db,
        )
    except Exception as e:
        log.error(
            f"add_files_to_knowledge_batch: Exception occurred: {e}", exc_info=True
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
```
**File:** backend/open_webui/retrieval/loaders/mistral.py (L486-514)
```python
    @asynccontextmanager
    async def _get_session(self):
        """Context manager for HTTP session with optimized settings."""
        connector = aiohttp.TCPConnector(
            limit=20,  # Increased total connection limit for better throughput
            limit_per_host=10,  # Increased per-host limit for API endpoints
            ttl_dns_cache=600,  # Longer DNS cache TTL (10 minutes)
            use_dns_cache=True,
            keepalive_timeout=60,  # Increased keepalive for connection reuse
            enable_cleanup_closed=True,
            force_close=False,  # Allow connection reuse
            resolver=aiohttp.AsyncResolver(),  # Use async DNS resolver
        )

        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=30,  # Connection timeout
            sock_read=60,  # Socket read timeout
        )

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": "OpenWebUI-MistralLoader/2.0"},
            raise_for_status=False,  # We handle status codes manually
            trust_env=True,
        ) as session:
            yield session

```
**File:** backend/open_webui/retrieval/loaders/mistral.py (L515-591)
```python
    def _process_results(self, ocr_response: Dict[str, Any]) -> List[Document]:
        """Process OCR results into Document objects with enhanced metadata and memory efficiency."""
        pages_data = ocr_response.get("pages")
        if not pages_data:
            log.warning("No pages found in OCR response.")
            return [
                Document(
                    page_content="No text content found",
                    metadata={"error": "no_pages", "file_name": self.file_name},
                )
            ]

        documents = []
        total_pages = len(pages_data)
        skipped_pages = 0

        # Process pages in a memory-efficient way
        for page_data in pages_data:
            page_content = page_data.get("markdown")
            page_index = page_data.get("index")  # API uses 0-based index

            if page_content is None or page_index is None:
                skipped_pages += 1
                self._debug_log(
                    f"Skipping page due to missing 'markdown' or 'index'. Data keys: {list(page_data.keys())}"
                )
                continue

            # Clean up content efficiently with early exit for empty content
            if isinstance(page_content, str):
                cleaned_content = page_content.strip()
            else:
                cleaned_content = str(page_content).strip()

            if not cleaned_content:
                skipped_pages += 1
                self._debug_log(f"Skipping empty page {page_index}")
                continue

            # Create document with optimized metadata
            documents.append(
                Document(
                    page_content=cleaned_content,
                    metadata={
                        "page": page_index,  # 0-based index from API
                        "page_label": page_index + 1,  # 1-based label for convenience
                        "total_pages": total_pages,
                        "file_name": self.file_name,
                        "file_size": self.file_size,
                        "processing_engine": "mistral-ocr",
                        "content_length": len(cleaned_content),
                    },
                )
            )

        if skipped_pages > 0:
            log.info(
                f"Processed {len(documents)} pages, skipped {skipped_pages} empty/invalid pages"
            )

        if not documents:
            # Case where pages existed but none had valid markdown/index
            log.warning(
                "OCR response contained pages, but none had valid content/index."
            )
            return [
                Document(
                    page_content="No valid text content found in document",
                    metadata={
                        "error": "no_valid_pages",
                        "total_pages": total_pages,
                        "file_name": self.file_name,
                    },
                )
            ]

        return documents
```
**File:** backend/open_webui/tools/builtin.py (L1611-1654)
```python
async def query_knowledge_files(
    query: str,
    knowledge_ids: Optional[list[str]] = None,
    count: int = 5,
    __request__: Request = None,
    __user__: dict = None,
    __model_knowledge__: list[dict] = None,
) -> str:
    """
    Search knowledge base files using semantic/vector search. Searches across collections (KBs),
    individual files, and notes that the user has access to.

    :param query: The search query to find semantically relevant content
    :param knowledge_ids: Optional list of KB ids to limit search to specific knowledge bases
    :param count: Maximum number of results to return (default: 5)
    :return: JSON with relevant chunks containing content, source filename, and relevance score
    """
    if __request__ is None:
        return json.dumps({"error": "Request context not available"})

    if not __user__:
        return json.dumps({"error": "User context not available"})

    # Coerce parameters from LLM tool calls (may come as strings)
    if isinstance(count, str):
        try:
            count = int(count)
        except ValueError:
            count = 5  # Default fallback

    # Handle knowledge_ids being string "None", "null", or empty
    if isinstance(knowledge_ids, str):
        if knowledge_ids.lower() in ("none", "null", ""):
            knowledge_ids = None
        else:
            # Try to parse as JSON array if it looks like one
            try:
                knowledge_ids = json.loads(knowledge_ids)
            except json.JSONDecodeError:
                # Treat as single ID
                knowledge_ids = [knowledge_ids]

    try:
        from open_webui.models.knowledge import Knowledges
```
**File:** backend/open_webui/tools/builtin.py (L1752-1781)
```python
        chunks = []

        # Add note results first
        chunks.extend(note_results)

        # Query vector collections if any
        if collection_names:
            query_results = await query_collection(
                collection_names=collection_names,
                queries=[query],
                embedding_function=embedding_function,
                k=count,
            )

            if query_results and "documents" in query_results:
                documents = query_results.get("documents", [[]])[0]
                metadatas = query_results.get("metadatas", [[]])[0]
                distances = query_results.get("distances", [[]])[0]

                for idx, doc in enumerate(documents):
                    chunk_info = {
                        "content": doc,
                        "source": metadatas[idx].get(
                            "source", metadatas[idx].get("name", "Unknown")
                        ),
                        "file_id": metadatas[idx].get("file_id", ""),
                    }
                    if idx < len(distances):
                        chunk_info["distance"] = distances[idx]
                    chunks.append(chunk_info)
```
**File:** backend/open_webui/retrieval/web/utils.py (L551-633)
```python
class SafeWebBaseLoader(WebBaseLoader):
    """WebBaseLoader with enhanced error handling for URLs."""

    def __init__(self, trust_env: bool = False, *args, **kwargs):
        """Initialize SafeWebBaseLoader
        Args:
            trust_env (bool, optional): set to True if using proxy to make web requests, for example
                using http(s)_proxy environment variables. Defaults to False.
        """
        super().__init__(*args, **kwargs)
        self.trust_env = trust_env

    async def _fetch(
        self, url: str, retries: int = 3, cooldown: int = 2, backoff: float = 1.5
    ) -> str:
        async with aiohttp.ClientSession(trust_env=self.trust_env) as session:
            for i in range(retries):
                try:
                    kwargs: Dict = dict(
                        headers=self.session.headers,
                        cookies=self.session.cookies.get_dict(),
                    )
                    if not self.session.verify:
                        kwargs["ssl"] = False

                    async with session.get(
                        url,
                        **(self.requests_kwargs | kwargs),
                        allow_redirects=False,
                    ) as response:
                        if self.raise_for_status:
                            response.raise_for_status()
                        return await response.text()
                except aiohttp.ClientConnectionError as e:
                    if i == retries - 1:
                        raise
                    else:
                        log.warning(
                            f"Error fetching {url} with attempt "
                            f"{i + 1}/{retries}: {e}. Retrying..."
                        )
                        await asyncio.sleep(cooldown * backoff**i)
        raise ValueError("retry count exceeded")

    def _unpack_fetch_results(
        self, results: Any, urls: List[str], parser: Union[str, None] = None
    ) -> List[Any]:
        """Unpack fetch results into BeautifulSoup objects."""
        from bs4 import BeautifulSoup

        final_results = []
        for i, result in enumerate(results):
            url = urls[i]
            if parser is None:
                if url.endswith(".xml"):
                    parser = "xml"
                else:
                    parser = self.default_parser
                self._check_parser(parser)
            final_results.append(BeautifulSoup(result, parser, **self.bs_kwargs))
        return final_results

    async def ascrape_all(
        self, urls: List[str], parser: Union[str, None] = None
    ) -> List[Any]:
        """Async fetch all urls, then return soups for all results."""
        results = await self.fetch_all(urls)
        return self._unpack_fetch_results(results, urls, parser=parser)

    def lazy_load(self) -> Iterator[Document]:
        """Lazy load text from the url(s) in web_path with error handling."""
        for path in self.web_paths:
            try:
                soup = self._scrape(path, bs_kwargs=self.bs_kwargs)
                text = soup.get_text(**self.bs_get_text_kwargs)

                # Build metadata
                metadata = extract_metadata(soup, path)

                yield Document(page_content=text, metadata=metadata)
            except Exception as e:
                # Log the error and continue with the next URL
                log.exception(f"Error loading {path}: {e}")
```
