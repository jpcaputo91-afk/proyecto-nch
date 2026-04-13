"""
RAG de Laudos CIADI — Proyecto NCH
Indexa todos los PDFs descargados y permite hacer consultas en lenguaje natural.
"""
import os, sys, json, re
import chromadb
from chromadb.utils import embedding_functions
from pdfminer.high_level import extract_text

BASE_LAUDOS = "/Users/juancaputo/Desktop/Proyecto nch/tesis-ciadi/laudos"
DB_PATH     = "/Users/juancaputo/Desktop/Proyecto nch/tesis-ciadi/rag-db"
LOG_IDX     = "/Users/juancaputo/Desktop/Proyecto nch/tesis-ciadi/rag-index-log.json"

# Función de embeddings — usa modelo multilingüe liviano (corre offline en M3)
EMB_FN = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="paraphrase-multilingual-MiniLM-L12-v2"
)

def get_client():
    return chromadb.PersistentClient(path=DB_PATH)

def get_collection(client):
    return client.get_or_create_collection(
        name="laudos_ciadi",
        embedding_function=EMB_FN,
        metadata={"hnsw:space": "cosine"}
    )

def chunk_text(texto, chunk_size=800, overlap=150):
    """Divide el texto en chunks con overlap para mejor recuperación."""
    words = texto.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+chunk_size])
        if len(chunk.strip()) > 100:
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks

def indexar_todos():
    """Indexa todos los PDFs disponibles."""
    client     = get_client()
    collection = get_collection(client)
    log_idx    = json.load(open(LOG_IDX)) if os.path.exists(LOG_IDX) else {}

    pdfs_todos = []
    for root, dirs, files in os.walk(BASE_LAUDOS):
        for f in files:
            if f.endswith(".pdf"):
                pdfs_todos.append(os.path.join(root, f))

    print(f"PDFs encontrados: {len(pdfs_todos)}")
    print(f"Ya indexados:     {len(log_idx)}")
    print(f"Por indexar:      {len(pdfs_todos) - len([p for p in pdfs_todos if p in log_idx])}")

    indexados = 0
    errores   = 0

    for i, pdf_path in enumerate(pdfs_todos):
        if pdf_path in log_idx:
            continue

        # Extraer metadata del path
        partes  = pdf_path.replace(BASE_LAUDOS+"/","").split("/")
        region  = partes[0] if len(partes) > 0 else "desconocida"
        caso    = partes[1] if len(partes) > 1 else "desconocido"
        archivo = partes[2] if len(partes) > 2 else partes[-1]
        year    = caso[:4] if caso[:4].isdigit() else "0000"

        try:
            texto = extract_text(pdf_path)
            if len(texto.strip()) < 200:
                log_idx[pdf_path] = {"ok": False, "error": "sin texto"}
                continue

            chunks = chunk_text(texto)
            if not chunks:
                log_idx[pdf_path] = {"ok": False, "error": "sin chunks"}
                continue

            ids       = [f"{caso}__{archivo}__{j}" for j in range(len(chunks))]
            metadatas = [{
                "caso":    caso,
                "region":  region,
                "archivo": archivo,
                "year":    year,
                "pdf_path":pdf_path,
                "chunk":   j,
            } for j in range(len(chunks))]

            # Insertar en lotes de 50
            for start in range(0, len(chunks), 50):
                collection.add(
                    documents=ids[start:start+50],
                    ids=ids[start:start+50],
                    metadatas=metadatas[start:start+50],
                )
                # Guardar el texto real aparte (ChromaDB guarda IDs, el texto lo mapeamos nosotros)
                for doc_id, chunk_txt in zip(ids[start:start+50], chunks[start:start+50]):
                    pass  # los embeddings se guardan, el texto se recupera por ID

            # Guardar también el texto chunkeado para recuperación
            chunk_store_path = pdf_path.replace(".pdf", "_chunks.json")
            with open(chunk_store_path, "w", encoding="utf-8") as f:
                json.dump({"chunks": chunks, "ids": ids}, f, ensure_ascii=False)

            log_idx[pdf_path] = {"ok": True, "chunks": len(chunks), "caso": caso}
            indexados += 1

            if indexados % 20 == 0:
                json.dump(log_idx, open(LOG_IDX,"w"), ensure_ascii=False, indent=2)
                print(f"  [{i+1}/{len(pdfs_todos)}] Indexados: {indexados} | Errores: {errores}")

        except Exception as e:
            log_idx[pdf_path] = {"ok": False, "error": str(e)[:100]}
            errores += 1

    json.dump(log_idx, open(LOG_IDX,"w"), ensure_ascii=False, indent=2)
    print(f"\nIndexación completa: {indexados} PDFs | {errores} errores")
    print(f"Total en colección: {collection.count()} chunks")
    return collection

def consultar(pregunta, n_resultados=8):
    """Hace una consulta en lenguaje natural sobre los laudos."""
    client     = get_client()
    collection = get_collection(client)

    if collection.count() == 0:
        print("La base aún no tiene documentos indexados. Corré indexar_todos() primero.")
        return

    results = collection.query(
        query_texts=[pregunta],
        n_results=min(n_resultados, collection.count()),
        include=["metadatas","distances"]
    )

    print(f"\n{'='*60}")
    print(f"CONSULTA: {pregunta}")
    print(f"{'='*60}")

    vistos = set()
    for meta, dist in zip(results["metadatas"][0], results["distances"][0]):
        caso = meta.get("caso","")
        if caso in vistos: continue
        vistos.add(caso)
        region  = meta.get("region","")
        pdf     = meta.get("pdf_path","")
        relevancia = round((1-dist)*100, 1)
        print(f"\n  Caso:      {caso}")
        print(f"  Región:    {region}")
        print(f"  Relevancia:{relevancia}%")
        print(f"  PDF:       {pdf[-60:]}")

        # Recuperar texto del chunk
        chunk_file = pdf.replace(".pdf","_chunks.json")
        if os.path.exists(chunk_file):
            data   = json.load(open(chunk_file, encoding="utf-8"))
            chunk_n= meta.get("chunk", 0)
            if chunk_n < len(data["chunks"]):
                fragmento = data["chunks"][chunk_n][:400]
                print(f"  Fragmento: {fragmento}...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "indexar":
        indexar_todos()
    elif len(sys.argv) > 1:
        consultar(" ".join(sys.argv[1:]))
    else:
        print("Uso:")
        print("  python3 rag-laudos.py indexar          → indexa todos los PDFs")
        print("  python3 rag-laudos.py 'tu pregunta'    → hace una consulta")
