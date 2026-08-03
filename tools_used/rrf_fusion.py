#making our rrf_fusion[Reciprocal Rank Fusion] algorithm to combine the result of semantic(similarity search) and bm25

from collections import defaultdict
def rrf_fusion(results, k=60):
    scores = defaultdict(float)
    for docs in results:
        for rank, doc in enumerate(docs, start=1):
            scores[doc.page_content] += 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)