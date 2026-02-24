import os
import markdown
import json
import re
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox
import urllib.parse

# Global variables to store directories
vault_dir = None
output_dir = None

def parse_vault(vault_dir):
    notes = {}
    links = defaultdict(list)
    
    for root, _, files in os.walk(vault_dir):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                # Calculate the web URL for this note
                rel_path = os.path.relpath(file_path, vault_dir)
                web_path = rel_path.replace('.md', '/').replace('\\', '/')
                if web_path.endswith('index/'):
                    web_path = web_path.replace('index/', '')
                
                # Full URL for your specific GitHub site
                full_url = "https://gitbrry.github.io/Campaign-Wiki/" + urllib.parse.quote(web_path)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    notes[file.lower()] = {
                        "content": content, 
                        "url": full_url,
                        "rel_path": file.lower()
                    }

                    link_patterns = [r'\[\[(.*?)\]\]']
                    for pattern in link_patterns:
                        for match in re.finditer(pattern, content):
                            link = match.group(1).split('|')[0].split('#')[0].strip().lower()
                            if not link.endswith('.md'):
                                link += '.md'
                            links[file.lower()].append(link)

    return notes, links

def generate_graph_data(notes, links):
    nodes = []
    for note_id, data in notes.items():
        label = note_id.replace('.md', '').capitalize()
        nodes.append({
            "id": note_id, 
            "label": label, 
            "url": data["url"],
            "link_count": 0
        })
    
    edges = []
    for src, dst_list in links.items():
        for dst in dst_list:
            if dst in notes:
                edges.append({"source": src, "target": dst})
                # Update link counts for sizing
                for n in nodes:
                    if n["id"] == src or n["id"] == dst:
                        n["link_count"] += 1

    return nodes, edges

def create_html_file(nodes, edges, output_dir):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body { margin: 0; padding: 0; overflow: hidden; background-color: #1e1e1e; }
            .node { cursor: pointer; } /* Change cursor to hand on hover */
            .link { stroke: #999; stroke-opacity: 0.4; stroke-width: 1px; }
            text { font-family: 'Roboto', sans-serif; font-size: 12px; pointer-events: none; fill: #ffffff; text-shadow: 1px 1px 2px #000; }
            svg { width: 100vw; height: 100vh; }
        </style>
    </head>
    <body>
        <div id="graph"></div>
        <script src="https://d3js.org/d3.v5.min.js"></script>
        <script>
            var nodes = """ + json.dumps(nodes) + """;
            var links = """ + json.dumps(edges) + """;

            var width = window.innerWidth;
            var height = window.innerHeight;

            var svg = d3.select("#graph").append("svg")
                .attr("width", width).attr("height", height);
            var g = svg.append("g");

            svg.call(d3.zoom().scaleExtent([0.1, 4]).on("zoom", () => g.attr("transform", d3.event.transform)));

            var simulation = d3.forceSimulation(nodes)
                .force("link", d3.forceLink(links).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2))
                .on("tick", ticked);

            var link = g.append("g").selectAll("line").data(links).enter().append("line").attr("class", "link");

            var node = g.append("g").selectAll("circle").data(nodes).enter().append("circle")
                .attr("class", "node")
                .attr("r", d => 5 + Math.sqrt(d.link_count * 2))
                .attr("fill", "#888")
                .on("click", d => window.parent.location.href = d.url) // THE MAGIC LINE
                .call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));

            var text = g.append("g").selectAll("text").data(nodes).enter().append("text")
                .attr("dx", 12).attr("dy", ".35em").text(d => d.label);

            function ticked() {
                link.attr("x1", d => d.source.x).attr("y1", d => d.source.y).attr("x2", d => d.target.x).attr("y2", d => d.target.y);
                node.attr("cx", d => d.x).attr("cy", d => d.y);
                text.attr("x", d => d.x).attr("y", d => d.y);
            }

            function dragstarted(d) { if (!d3.event.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; }
            function dragged(d) { d.fx = d3.event.x; d.fy = d3.event.y; }
            function dragended(d) { if (!d3.event.active) simulation.alphaTarget(0); d.fx = null; d.fy = null; }
        </script>
    </body>
    </html>
    """
    output_file = os.path.join(output_dir, 'vault_graph.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

def create_html():
    global vault_dir, output_dir
    if not vault_dir or not output_dir:
        messagebox.showerror("Error", "Select directories first!")
        return
    notes, links = parse_vault(vault_dir)
    nodes, edges = generate_graph_data(notes, links)
    create_html_file(nodes, edges, output_dir)
    messagebox.showinfo("Success", "Graph updated with clickable links!")

root = tk.Tk()
root.title("DM Graph Generator")
tk.Button(root, text="1. Select 'docs' folder", command=lambda: globals().update(vault_dir=filedialog.askdirectory())).pack(pady=5)
tk.Button(root, text="2. Select 'docs/assets' folder", command=lambda: globals().update(output_dir=filedialog.askdirectory())).pack(pady=5)
tk.Button(root, text="3. Create Clickable Graph", command=create_html).pack(pady=10)
root.mainloop()