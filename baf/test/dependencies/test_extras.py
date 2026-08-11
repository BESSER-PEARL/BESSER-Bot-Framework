"""Smoke tests for every dependency in requirements-extras.txt."""

import pytest


def test_spacy():
    spacy = pytest.importorskip("spacy")
    nlp = spacy.blank("en")
    doc = nlp("hello world")
    assert [t.text for t in doc] == ["hello", "world"]


def test_sklearn():
    sklearn = pytest.importorskip("sklearn")
    from sklearn.linear_model import LinearRegression
    from sklearn.datasets import make_regression
    X, y = make_regression(n_samples=10, n_features=2, random_state=0)
    model = LinearRegression().fit(X, y)
    assert model.predict(X).shape == (10,)
    assert sklearn.__version__


def test_librosa():
    librosa = pytest.importorskip("librosa")
    assert librosa.__version__


def test_speech_recognition():
    sr = pytest.importorskip("speech_recognition")
    assert sr.Recognizer()


def test_soundfile():
    sf = pytest.importorskip("soundfile")
    import numpy as np
    import io
    buf = io.BytesIO()
    data = np.zeros(16, dtype=np.float32)
    sf.write(buf, data, 16000, format="WAV")
    buf.seek(0)
    read_data, samplerate = sf.read(buf)
    assert samplerate == 16000
    assert len(read_data) == 16


def test_opencv():
    cv2 = pytest.importorskip("cv2")
    import numpy as np
    img = np.zeros((4, 4, 3), dtype=np.uint8)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    assert gray.shape == (4, 4)


def test_plotly():
    plotly = pytest.importorskip("plotly")
    import plotly.graph_objs as go
    fig = go.Figure(data=[go.Bar(x=[1, 2], y=[3, 4])])
    assert len(fig.data) == 1
    assert plotly.__version__


def test_chromadb():
    chromadb = pytest.importorskip("chromadb")
    client = chromadb.EphemeralClient()
    collection = client.create_collection("smoke_test")
    collection.add(ids=["a"], documents=["hello"])
    assert collection.count() == 1


def test_langchain():
    pytest.importorskip("langchain")
    from langchain.prompts import PromptTemplate
    tpl = PromptTemplate.from_template("Hi {name}")
    assert tpl.format(name="Ana") == "Hi Ana"


def test_langchain_community():
    lc_community = pytest.importorskip("langchain_community")
    assert lc_community


def test_pypdf():
    pypdf = pytest.importorskip("pypdf")
    assert pypdf.PdfReader
    assert pypdf.PdfWriter


def test_tiktoken():
    tiktoken = pytest.importorskip("tiktoken")
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode("hello world")
    assert enc.decode(tokens) == "hello world"


def test_rank_bm25():
    rank_bm25 = pytest.importorskip("rank_bm25")
    assert rank_bm25.BM25Okapi


def test_hybrid_rag():
    pytest.importorskip("rank_bm25")
    from baf.nlp.rag.rag import HybridRAG
    assert HybridRAG
