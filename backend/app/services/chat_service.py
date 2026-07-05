import logging
from openai import OpenAI
import re
from typing import Dict, Any, List
from app.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE

logger = logging.getLogger(__name__)

class ChatService:
    @classmethod
    def answer_query(cls, query: str, df_summary: Dict[str, Any], quality_score: float, chat_history: List[Any] = []) -> str:
        """Answers dataset questions using an LLM if keys exist, otherwise falls back to a regex keyword matcher."""
        
        # 1. Attempt LLM-based Chat if an API key is configured
        if OPENAI_API_KEY:
            try:
                return cls.chat_openai(query, df_summary, quality_score, chat_history)
            except Exception as e:
                logger.error(f"LLM chat failed. Error: {str(e)}")

        # 2. Local fallback chatbot (Regex & statistical parsing)
        return cls.chat_local(query, df_summary, quality_score)

    @classmethod
    def _get_system_instruction(cls, df_summary: Dict[str, Any], quality_score: float) -> str:
        # Create a compressed representation of statistics
        stats_clean = {
            "shape": df_summary["shape"],
            "quality_score": quality_score,
            "columns": list(df_summary["dtypes"].keys()),
            "datatypes": df_summary["dtypes"],
            "null_counts": df_summary["null_summary"],
            "strong_correlations": df_summary["correlation"].get("strong_relationships", []),
            "descriptive_stats_summary": {
                k: {
                    "mean": v.get("mean"),
                    "median": v.get("median"),
                    "min": v.get("min"),
                    "max": v.get("max"),
                    "most_frequent": v.get("most_frequent") or v.get("mode")
                }
                for k, v in df_summary["descriptive_stats"].items()
            }
        }
        
        return f"""
You are a friendly, highly intelligent AI Data Analyst assistant for the DataInsight AI platform.
You are helping a user analyze their uploaded dataset.
Here are the statistical profile summaries of the active dataset version:
{stats_clean}

Please answer the user's questions clearly, concisely, and professionally. Quote precise values, statistics, or columns from the metadata where appropriate. 
If the user asks for actions (like "remove columns"), explain how to do it using the Cleaning panel in the app.
"""

    @classmethod
    def chat_openai(cls, query: str, df_summary: Dict[str, Any], quality_score: float, chat_history: List[Any]) -> str:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        messages = [
            {"role": "system", "content": cls._get_system_instruction(df_summary, quality_score)}
        ]
        
        # Feed history
        for msg in chat_history[-10:]:
            role = "user" if msg.sender == "user" else "assistant"
            messages.append({"role": role, "content": msg.message})
            
        messages.append({"role": "user", "content": query})
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=LLM_TEMPERATURE
        )
        return response.choices[0].message.content.strip()

    @classmethod
    def chat_local(cls, query: str, df_summary: Dict[str, Any], quality_score: float) -> str:
        """Fallback keyword-matching engine responding to typical dataset questions."""
        q = query.lower()

        # 1. Summarize
        if any(w in q for w in ["summar", "overview", "describe", "profile", "tell me about"]):
            shape = df_summary["shape"]
            cols_desc = ", ".join([f"{k} ({v})" for k, v in df_summary["dtypes"].items()])
            return (
                f"### Dataset Summary\n"
                f"- **Dimensions**: {shape[0]} rows and {shape[1]} columns.\n"
                f"- **Data Quality Score**: {quality_score}/100.\n"
                f"- **Memory Footprint**: {df_summary['memory_usage']}.\n"
                f"- **Columns**: {cols_desc}.\n\n"
                f"Navigate to the **EDA** tab to view complete statistics and visual plots, or the **Cleaning** tab to resolve outstanding flags."
            )

        # 2. Missing values
        if any(w in q for w in ["missing", "null", "empty", "na "]):
            nulls = df_summary["null_summary"]
            active_nulls = {k: v for k, v in nulls.items() if v > 0}
            if not active_nulls:
                return "Good news! There are **no missing values** detected anywhere in the active dataset version."
            
            summary_list = "\n".join([f"- **{col}**: {cnt} missing entries ({cnt/df_summary['shape'][0]*100:.1f}%)" for col, cnt in active_nulls.items()])
            most_null_col = max(nulls, key=nulls.get)
            most_null_cnt = nulls[most_null_col]
            
            return (
                f"### Missing Values Report\n"
                f"The active version contains missing values in the following fields:\n"
                f"{summary_list}\n\n"
                f"**Column with highest missing count**: '{most_null_col}' ({most_null_cnt} missing values).\n"
                f"You can impute these missing variables under the **Cleaning** tab using Mean, Median, Mode, or FFill/BFill strategies."
            )

        # 3. Correlations
        if any(w in q for w in ["correlat", "relation", "heatmap"]):
            strong_corrs = df_summary["correlation"].get("strong_relationships", [])
            if not strong_corrs:
                return (
                    "There are **no strong linear correlations** ($|r| \\ge 0.7$) detected between numerical variables in this dataset.\n"
                    "You can inspect the full correlation matrix grid inside the **EDA** visualization page."
                )
            
            corr_list = "\n".join([
                f"- **{c['column1']}** & **{c['column2']}**: {c['coefficient']:.2f} ({c['direction']} correlation)"
                for c in strong_corrs
            ])
            return (
                f"### Correlation Analysis\n"
                f"I've identified these strong relationships among numerical columns:\n"
                f"{corr_list}\n\n"
                f"These values indicate linear dependencies. You can examine the full Pearson correlation heatmap in the **EDA** tab."
            )

        # 4. Outliers
        if any(w in q for w in ["outlier", "anomaly", "skew"]):
            # Count outliers
            num_cols = [k for k, v in df_summary["dtypes"].items() if v == "numeric"]
            outlier_details = []
            for col in num_cols:
                stats = df_summary["descriptive_stats"].get(col, {})
                if stats and stats.get("count", 0) > 0:
                    # Look at IQR
                    q25 = stats.get("q25", 0)
                    q75 = stats.get("q75", 0)
                    iqr = q75 - q25
                    lower = q25 - 1.5 * iqr
                    upper = q75 + 1.5 * iqr
                    min_val = stats.get("min", 0)
                    max_val = stats.get("max", 0)
                    if min_val < lower or max_val > upper:
                        outlier_details.append(f"'{col}' (ranges outside [{lower:.2f}, {upper:.2f}])")

            if not outlier_details:
                return "Based on standard IQR checks ($1.5 \\times IQR$), there are no extreme outliers in your numerical columns."
            
            cols_str = ", ".join(outlier_details)
            return (
                f"### Outlier Scan\n"
                f"Numerical columns showing potential outliers based on IQR limits: {cols_str}.\n\n"
                f"You can cap or filter out these values using the **Outliers** form inside the **Cleaning** workstation."
            )

        # 5. Which columns to remove
        if any(w in q for w in ["remove", "delete", "drop", "discard"]):
            nulls = df_summary["null_summary"]
            suggestions = []
            
            # High null counts
            row_count = df_summary["shape"][0]
            for col, count in nulls.items():
                if count / row_count > 0.5:
                    suggestions.append(f"**{col}** - Very high missing percentage ({count/row_count*100:.1f}% missing). Better to drop.")
            
            # ID columns (100% unique and textual/categorical, which usually are metadata keys, not statistical features)
            for col, stats in df_summary["descriptive_stats"].items():
                if stats.get("type") == "categorical":
                    unique = stats.get("unique_count", 0)
                    count = stats.get("count", 0)
                    if unique == count and count > 10:
                        suggestions.append(f"**{col}** - 100% unique row values (likely a primary key or unique text ID). Safe to remove for statistical correlations.")

            if not suggestions:
                return (
                    "Every column in your dataset appears to have solid informational value. "
                    "However, if you have metadata fields like record IDs or timestamps that aren't useful in your predictive models, "
                    "you can delete them in the **Cleaning -> Column Operations** sidebar."
                )
            
            sugg_str = "\n".join([f"- {s}" for s in suggestions])
            return (
                f"### Column Removal Suggestions\n"
                f"Based on dataset metrics, you might consider removing:\n"
                f"{sugg_str}\n\n"
                f"To delete columns, open the **Cleaning** workstation and use the **Delete Column** operation."
            )

        # Default Response
        return (
            "Hello! I am your local AI Assistant.\n"
            "I'm operating in statistical fallback mode because no external API key (`OPENAI_API_KEY`) is defined.\n\n"
            "I can answer queries related to:\n"
            "- **Summarizing the dataset** (\"tell me about my data\", \"summarize this dataset\")\n"
            "- **Missing values** (\"which columns have nulls?\", \"most missing values\")\n"
            "- **Correlations** (\"what are the strongest correlations?\", \"show relationships\")\n"
            "- **Outliers** (\"are there any outliers?\", \"anomalies\")\n"
            "- **Column pruning** (\"which columns should I remove?\")\n\n"
            "What would you like to investigate?"
        )
