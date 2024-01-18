from langchain_community.document_loaders import WebBaseLoader


class WebDownloader:
    def download(self, url):
        loader = WebBaseLoader(url, bs_get_text_kwargs={"separator": " "})
        docs = loader.load()
        return docs[0].page_content


__all__ = ["WebDownloader"]
