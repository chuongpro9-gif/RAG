import json

class SecureRetriever:
    def __init__(self, base_retriever):
        """
        Wraps any retriever (BM25, Dense, Hybrid) and filters the output based on roles.
        Assumes `df` used to build the retriever has 'allowed_roles' JSON string column,
        or metadata returned by retrieve() contains 'allowed_roles'.
        """
        self.base_retriever = base_retriever

    def retrieve(self, query, user_roles, top_k=5):
        # We need to fetch more from base because some will be filtered out
        raw_results = self.base_retriever.retrieve(query, top_k=top_k * 3)
        
        filtered_results = []
        for res in raw_results:
            metadata = res.get("metadata", {})
            allowed_roles_str = metadata.get("allowed_roles", '["Admin"]')
            if isinstance(allowed_roles_str, str):
                try:
                    allowed_roles = json.loads(allowed_roles_str)
                except:
                    allowed_roles = ["Admin"]
            else:
                allowed_roles = allowed_roles_str
                
            # Check intersection
            if any(role in user_roles for role in allowed_roles):
                filtered_results.append(res)
                if len(filtered_results) >= top_k:
                    break
                    
        return filtered_results
