from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import os
import numpy as np
from itertools import combinations
from pathlib import Path
app = Flask(__name__)
# Enhance CORS configuration (to avoid cross-domain issues)
CORS(app)
CURRENT_DIR = Path(__file__).resolve().parent  
# --------------------------
# Core utility function: Converts NumPy types to native Python types (solves JSON serialization issues).
# --------------------------
def convert_numpy_types(obj):
    """Recursively converts NumPy types to native Python types (solves JSON serialization issues)."""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj


# --------------------------
# Utility function: Clean the author_position field (resolves non-numeric value issues)
# --------------------------
def clean_author_position(position):
    """
    Clean the author_position field to ensure it contains only numeric values.
    - Numeric strings (e.g., '1') are converted to integers.
    - Non-numeric strings (e.g., 'middle'/'last') are mapped to reasonable values.
    - Unrecognized values are returned as None (for later filtering).
    """
    if pd.isna(position):
        return None
    
    try:
        return int(position)
    except (ValueError, TypeError):
        # Handling non-numeric strings (common scenarios: 'middle' = intermediate author, 'last' = corresponding author)
        position_str = str(position).strip().lower()
        if position_str in ["middle", "mid"]:
            return 2  # Intermediate authors are mapped to 2
        elif position_str in ["last", "corresponding", "corr"]:
            return -1  # Corresponding authors are mapped to -1 (for later identification)
        else:
            # Unrecognized values (e.g., 'unknown') are returned as None (for later filtering)
            return None



def generate_citation_network():
    csv_path = CURRENT_DIR/"refs_yeshiva_cs_20_25.csv"  
    if not os.path.exists(csv_path):
        return convert_numpy_types({
            "error": f"The CSV file for the citation network could not be found. Please check the path: {csv_path}",
            "nodes": [],
            "links": []
        })
    
    try:
       # Specify dtype as a native Python type when reading CSV (to avoid NumPy types)
        df = pd.read_csv(csv_path, dtype={
            "citing_paperid": str,
            "cited_paperid": str,
            "year": int,  # Force to Python int
            "ref_year": int  # Force to Python int
        })
        
        # Data Cleaning
        df_clean = df.dropna(subset=["citing_paperid", "cited_paperid", "year", "ref_year"])
        df_clean = df_clean[(df_clean["year"] >= 2020) & (df_clean["year"] <= 2025)]
        
        # Generate nodes 
        all_paper_ids = pd.concat([df_clean["citing_paperid"], df_clean["cited_paperid"]]).unique()
        nodes = []
        
        for paper_id in all_paper_ids:
            citing_records = df_clean[df_clean["citing_paperid"] == paper_id]
            cited_records = df_clean[df_clean["cited_paperid"] == paper_id]
            
            # Determine publication year (convert to native Python int)
            if not citing_records.empty:
                publish_year = int(citing_records["year"].iloc[0])
            elif not cited_records.empty:
                publish_year = int(cited_records["ref_year"].iloc[0])
            else:
                publish_year = "Unknown"
            
            # Count citations (convert to native Python int)
            citation_count = int(len(cited_records))
            
            nodes.append({
                "id": paper_id,
                "name": f"Paper_{paper_id}",
                "publish_year": publish_year,
                "citation_count": citation_count,
                "institution": "Yeshiva University, Computer Science Department"
            })
        
        # Generate edges (count citations)
        link_groups = df_clean.groupby(["cited_paperid", "citing_paperid"]).size().reset_index(name="citation_times")
        links = []
        
        for _, row in link_groups.iterrows():
            cited_id = row["cited_paperid"]
            citing_id = row["citing_paperid"]
            cite_times = int(row["citation_times"])  # Convert to native Python int
            
            if any(node["id"] == cited_id for node in nodes) and any(node["id"] == citing_id for node in nodes):
                citing_year = int(df_clean[df_clean["citing_paperid"] == citing_id]["year"].iloc[0])
                cited_year = int(df_clean[df_clean["cited_paperid"] == cited_id]["ref_year"].iloc[0])
                
                links.append({
                    "source": cited_id,
                    "target": citing_id,
                    "value": cite_times,
                    "citing_year": citing_year,
                    "cited_year": cited_year,
                    "year_diff": citing_year - cited_year  # Add year difference
                })
        
        # Key: Convert all numpy types to native Python types
        result = convert_numpy_types({
            "nodes": nodes,
            "links": links
        })
        return result
    
    except Exception as e:
        return convert_numpy_types({
            "error": f"Data processing failed: {str(e)}",
            "nodes": [],
            "links": []
        })


def generate_collaboration_network():
    affils_csv_path = CURRENT_DIR/"affils_yeshiva_cs_20_25.csv"
    if not os.path.exists(affils_csv_path):
        return convert_numpy_types({
            "error": f"The CSV file for the author collaboration network could not be found.：{affils_csv_path}",
            "nodes": [],
            "links": []
        })
    
    try:
 
        affils_df = pd.read_csv(affils_csv_path, dtype={
            "paperid": str,
            "authorid": str,
            "institutionid": str
        })
        
    
        sample_size = 1000
        if len(affils_df) > sample_size:
            unique_papers = affils_df["paperid"].unique()[:sample_size]
            affils_df = affils_df[affils_df["paperid"].isin(unique_papers)]
        
    
        df_clean = affils_df.copy()
        df_clean["author_position_clean"] = df_clean["author_position"].apply(clean_author_position)
        df_clean = df_clean.dropna(subset=["paperid", "authorid", "author_position_clean"])
        df_clean = df_clean[
            (df_clean["paperid"].str.strip() != "") & 
            (df_clean["authorid"].str.strip() != "")
        ]
        
      
        author_papers = df_clean.groupby("authorid")["paperid"].nunique().reset_index(name="papers_published")
        first_author_papers = df_clean[df_clean["author_position_clean"] == 1].groupby("authorid")["paperid"].nunique().reset_index(name="first_author_papers")
        corr_author_papers = df_clean[df_clean["author_position_clean"] == -1].groupby("authorid")["paperid"].nunique().reset_index(name="corr_author_papers")
        
        author_attrs = pd.merge(author_papers, first_author_papers, on="authorid", how="left").fillna({"first_author_papers": 0})
        author_attrs = pd.merge(author_attrs, corr_author_papers, on="authorid", how="left").fillna({"corr_author_papers": 0})
        author_attrs = author_attrs[author_attrs["papers_published"] >= 0]  
        
 
        nodes = []
        for _, row in author_attrs.iterrows():
            author_id = row["authorid"]
            nodes.append({
                "id": author_id,
                "name": f"Author_{author_id}",
                "department": "Yeshiva University, Computer Science Department",
                "papers_published": int(row["papers_published"]),
                "first_author_papers": int(row["first_author_papers"]),
                "corr_author_papers": int(row["corr_author_papers"]),
                "h_index": int(min(row["papers_published"], 15))
            })
        
      
        paper_authors = df_clean.groupby("paperid")["authorid"].apply(list).reset_index(name="authors")
        collaboration_pairs = []
        
        for _, row in paper_authors.iterrows():
            authors = sorted(row["authors"])
            if len(authors) >= 2:
                pairs = combinations(authors, 2)
                for pair in pairs:
                    collaboration_pairs.append({
                        "source_author": pair[0],
                        "target_author": pair[1],
                        "paperid": row["paperid"]
                    })
        
        collaboration_counts = pd.DataFrame(collaboration_pairs).groupby(
            ["source_author", "target_author"]
        ).size().reset_index(name="collaboration_times")
        
        node_ids = set(node["id"] for node in nodes)
        links = []
        for _, row in collaboration_counts.iterrows():
            source = row["source_author"]
            target = row["target_author"]
            collab_times = int(row["collaboration_times"])
            
            if source in node_ids and target in node_ids:
                links.append({
                    "source": source,
                    "target": target,
                    "value": collab_times,
                    "co_authored_papers": collab_times
                })
        
        return convert_numpy_types({"nodes": nodes, "links": links})
    
    except Exception as e:
        return convert_numpy_types({
            "error": f"Author collaboration network data processing failed：{str(e)}",
            "nodes": [],
            "links": []
        })
def generate_enhanced_citation_network():
    csv_path = CURRENT_DIR/"refs_yeshiva_cs_20_25.csv"  
    if not os.path.exists(csv_path):
        return convert_numpy_types({
            "error": f"The CSV file for the citation network could not be found. Please check the path: {csv_path}",
            "nodes": [],
            "links": []
        })
    
    try:
       
        df = pd.read_csv(csv_path, dtype={
            "citing_paperid": str,
            "cited_paperid": str,
            "year": int,  
            "ref_year": int  
        })
        
       
        df_clean = df.dropna(subset=["citing_paperid", "cited_paperid", "year", "ref_year"])
        df_clean = df_clean[(df_clean["year"] >= 2020) & (df_clean["year"] <= 2025)]
        
      
        all_paper_ids = pd.concat([df_clean["citing_paperid"], df_clean["cited_paperid"]]).unique()
        nodes = []
        
        for paper_id in all_paper_ids:
            citing_records = df_clean[df_clean["citing_paperid"] == paper_id]
            cited_records = df_clean[df_clean["cited_paperid"] == paper_id]
            
           
            if not citing_records.empty:
                publish_year = int(citing_records["year"].iloc[0])
            elif not cited_records.empty:
                publish_year = int(cited_records["ref_year"].iloc[0])
            else:
                publish_year = "Unknown"
            
            
            citation_count = int(len(cited_records))
            impact_score = citation_count * 0.8 + 2.0
            nodes.append({
                "id": paper_id,
                "name": f"Paper_{paper_id}",
                "publish_year": publish_year,
                "citation_count": citation_count,
                "institution": "Yeshiva University, Computer Science Department",
                "topic": "Computer Science",
                "impact_score": float(impact_score)
            })
        
     
        link_groups = df_clean.groupby(["cited_paperid", "citing_paperid"]).size().reset_index(name="citation_times")
        links = []
        
        for _, row in link_groups.iterrows():
            cited_id = row["cited_paperid"]
            citing_id = row["citing_paperid"]
            cite_times = int(row["citation_times"])  
            
            if any(node["id"] == cited_id for node in nodes) and any(node["id"] == citing_id for node in nodes):
                citing_year = int(df_clean[df_clean["citing_paperid"] == citing_id]["year"].iloc[0])
                cited_year = int(df_clean[df_clean["cited_paperid"] == cited_id]["ref_year"].iloc[0])
                
                links.append({
                    "source": cited_id,
                    "target": citing_id,
                    "value": cite_times,
                    "citing_year": citing_year,
                    "cited_year": cited_year,
                    "year_diff": citing_year - cited_year  
                })
        
       
        result = convert_numpy_types({
            "nodes": nodes,
            "links": links
        })
        return result
    
    except Exception as e:
        return convert_numpy_types({
            "error": f"Data processing failed: {str(e)}",
            "nodes": [],
            "links": []
        })
# --------------------------
# API Routing
# --------------------------
@app.route("/api/citation-network", methods=["GET"])
def get_citation_network():
    data = generate_citation_network()
    return jsonify(data)

@app.route("/api/collaboration-network", methods=["GET"])
def get_collaboration_network():
    return jsonify(generate_collaboration_network())


@app.route("/api/paper-counts", methods=["GET"])
def get_paper_counts():
    try:
      
        years = range(2014, 2024)  
        data = [{"year": year, "count": np.random.randint(5, 35)} for year in years]
        return jsonify(convert_numpy_types(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/patent-citations", methods=["GET"])
def get_patent_citations():
    try:
      
        data = [{"patentCount": i, "paperCount": np.random.randint(5, 55)} for i in range(15)]
        return jsonify(convert_numpy_types(data))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route("/api/enhanced-citation-network", methods=["GET"])
def get_enhanced_citation_network():
    data = generate_enhanced_citation_network()
    return jsonify(data)

# --------------------------
# Server On
# --------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)