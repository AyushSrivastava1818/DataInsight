import json
import logging
import re
from openai import OpenAI
from typing import List, Dict, Any
from app.config import OPENAI_API_KEY, LLM_MODEL, LLM_TEMPERATURE
from app.services.eda_service import EDAService

logger = logging.getLogger(__name__)

class InsightService:
    @classmethod
    def generate_insights(cls, df_summary: Dict[str, Any], quality_score: float) -> List[Dict[str, Any]]:
        """Generates structured insights using OpenAI or a robust rules-based local engine."""
        
        # 1. Attempt LLM-based Generation if an API key is configured
        if OPENAI_API_KEY:
            try:
                return cls.generate_insights_openai(df_summary, quality_score)
            except Exception as e:
                logger.error(f"LLM insight generation failed, falling back. Error: {str(e)}")

        # 2. Fallback: Rules-based local insight engine
        return cls.generate_local_insights(df_summary, quality_score)

    @classmethod
    def generate_local_insights(cls, df_summary: Dict[str, Any], quality_score: float) -> List[Dict[str, Any]]:
        """Heuristics engine generating natural-language business and statistical insights."""
        insights = []

        # A. Data Quality Insights
        if quality_score < 70:
            insights.append({
                "category": "anomaly",
                "title": "Low Data Quality Score Alert",
                "description": f"The dataset has a quality score of {quality_score}/100. This is driven by elevated levels of missing records, duplicate rows, or extreme numerical outliers. Review the Cleaning panel to resolve these issues.",
                "importance": "high"
            })
        else:
            insights.append({
                "category": "trend",
                "title": "Excellent Data Health",
                "description": f"Data quality score is healthy ({quality_score}/100). The dataset is clean, well-formed, and ready for modeling or deep analysis.",
                "importance": "medium"
            })

        # B. Missing Value Insights
        for col, null_count in df_summary["null_summary"].items():
            if null_count > 0:
                row_count = df_summary["shape"][0]
                pct = (null_count / row_count) * 100 if row_count > 0 else 0
                if pct > 15:
                    insights.append({
                        "category": "anomaly",
                        "title": f"High Missing Data: {col}",
                        "description": f"Column '{col}' is missing {null_count} values ({pct:.1f}% of rows). Consider using mean/median imputation, or drop the column if it's not critical.",
                        "importance": "high" if pct > 30 else "medium"
                    })

        # C. Correlation Insights
        strong_corrs = df_summary["correlation"].get("strong_relationships", [])
        for corr in strong_corrs[:3]:  # Top 3
            coef = corr["coefficient"]
            direction = corr["direction"]
            col1 = corr["column1"]
            col2 = corr["column2"]
            insights.append({
                "category": "correlation",
                "title": f"Strong Correlation: {col1} & {col2}",
                "description": f"'{col1}' and '{col2}' share a strong {direction} relationship (correlation coefficient: {coef:.2f}). Adjustments in one likely correspond to changes in the other.",
                "importance": "medium"
            })

        # D. Categorical Insights
        for col, details in df_summary["categorical_summary"].items():
            top_cats = details.get("top_categories", {})
            if top_cats:
                total_cat_rows = sum(top_cats.values())
                # Find the largest category
                first_cat = list(top_cats.keys())[0]
                first_count = top_cats[first_cat]
                pct = (first_count / total_cat_rows) * 100 if total_cat_rows > 0 else 0
                unique_count = details.get('unique_count', 0)
                if pct > 40 and unique_count > 1:
                    insights.append({
                        "category": "trend",
                        "title": f"Dominant Category in {col}",
                        "description": f"'{first_cat}' is the most frequent category in '{col}', accounting for {pct:.1f}% of all non-null records (out of {unique_count} distinct categories).",
                        "importance": "medium"
                    })

        # E. Outlier Insights (Check numerical distributions)
        for col, stats in df_summary["descriptive_stats"].items():
            if stats.get("type") == "numeric":
                mean = stats.get("mean", 0)
                median = stats.get("median", 0)
                std = stats.get("std", 0)
                if std > 0:
                    skewness_indicator = abs(mean - median) / std
                    if skewness_indicator > 0.5:
                        direction = "right-skewed (positive skew)" if mean > median else "left-skewed (negative skew)"
                        insights.append({
                            "category": "trend",
                            "title": f"Skewed Distribution: {col}",
                            "description": f"Column '{col}' exhibits a {direction} distribution (mean: {mean:.2f}, median: {median:.2f}). Median is likely a better measure of central tendency than the mean.",
                            "importance": "low"
                        })

        # F. Default generic recommendation if insights list is short
        if len(insights) < 3:
            insights.append({
                "category": "recommendation",
                "title": "Perform Feature Scaling",
                "description": "If planning to run machine learning or clustering models, ensure numerical variables are scaled (e.g. MinMax or Standard scaler) since features vary in standard deviations.",
                "importance": "low"
            })

        # Ensure recommendation is always present
        insights.append({
            "category": "recommendation",
            "title": "Download Cleaned CSV Report",
            "description": "Download the processed and cleaned dataset to use in your BI dashboards (Power BI/Tableau) or training scripts.",
            "importance": "medium"
        })

        return insights

    @classmethod
    def _get_llm_system_prompt(cls) -> str:
        return """
You are an expert Senior Data Analyst and Business Intelligence specialist.
Analyze the provided dataset summary statistics and generate a JSON array of actionable, highly professional business insights.
Each insight must be a JSON object with:
- "category": Choose from "trend", "anomaly", "correlation", "recommendation"
- "title": A concise bold title (e.g., "High Revenue Concentration", "Sales Q4 Spikes")
- "description": A 2-3 sentence analytical explanation citing specific variables, ratios, or values.
- "importance": Choose from "high", "medium", "low"

Provide EXACTLY a valid JSON array of objects. Do not wrap the JSON in Markdown backticks (e.g. do not output ```json ... ```) or any additional text. Return raw JSON text only.
"""

    @classmethod
    def _get_dataset_context_prompt(cls, df_summary: Dict[str, Any], quality_score: float) -> str:
        # Strip out extremely detailed dictionaries to keep token counts small
        clean_summary = {
            "shape": df_summary["shape"],
            "memory_usage": df_summary["memory_usage"],
            "quality_score": quality_score,
            "dtypes": df_summary["dtypes"],
            "null_summary": df_summary["null_summary"],
            "strong_correlations": df_summary["correlation"].get("strong_relationships", []),
            "descriptive_stats_truncated": {
                k: {
                    "mean": v.get("mean"),
                    "median": v.get("median"),
                    "min": v.get("min"),
                    "max": v.get("max"),
                    "std": v.get("std"),
                    "most_frequent": v.get("most_frequent") or v.get("mode")
                }
                for k, v in df_summary["descriptive_stats"].items()
            }
        }
        return f"Dataset Summary:\n{json.dumps(clean_summary, indent=2)}\n\nGenerate analytical insights."

    @classmethod
    def generate_insights_openai(cls, df_summary: Dict[str, Any], quality_score: float) -> List[Dict[str, Any]]:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = cls._get_dataset_context_prompt(df_summary, quality_score)
        
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": cls._get_llm_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            temperature=LLM_TEMPERATURE
        )
        text = response.choices[0].message.content.strip()
        
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

        return json.loads(text)
