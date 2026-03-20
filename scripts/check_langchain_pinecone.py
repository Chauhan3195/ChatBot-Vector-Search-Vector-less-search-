import importlib.util

print("spec(langchain_pinecone) =", importlib.util.find_spec("langchain_pinecone"))
import langchain_pinecone  # noqa: F401

try:
    import importlib.metadata as m

    print("langchain-pinecone version =", m.version("langchain-pinecone"))
except Exception as e:
    print("could not read version:", e)

