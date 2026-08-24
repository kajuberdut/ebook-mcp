# Tutorial: Using MCP Inspector to Understand `ebook-mcp`

This tutorial provides a high-level overview of the **Model Context Protocol (MCP)** and a step-by-step walkthrough for using the official **MCP Inspector** web UI to explore and debug the `ebook-mcp` server.

---

## 1. What is the Model Context Protocol (MCP)?

The **Model Context Protocol (MCP)** is an open standard designed to seamlessly connect AI models (such as Claude, GPT, or custom LLM agents) with external tools, data sources, and services.

Rather than writing custom API wrappers for every LLM client, MCP standardizes how AI applications discover and interact with capabilities provided by a server.

### Core MCP Primitives

1. **Tools**: Executable functions exposed to the AI model (e.g. `get_all_epub_files`, `get_epub_toc`, `get_epub_chapter_markdown`). The server defines input JSON schemas, parameter requirements, and tool descriptions so the LLM knows when and how to invoke them.
2. **Prompts**: Reusable prompt templates (e.g. `summarize_chapter`, `generate_quiz`) that guide the LLM's interactions with tools.
3. **Resources**: Data or file URIs exposed directly to LLMs for reading structured context.
4. **Transports**: Communication protocols connecting client and server:
   - **`stdio`**: Standard Input/Output communication, used when running locally as a CLI subprocess.
   - **`sse` (Server-Sent Events)**: HTTP-based streaming communication, used in containerized or remote deployments (such as Docker Compose).

---

## 2. Launching MCP Inspector with Docker Compose

`ebook-mcp` includes a bundled Docker Compose mix-in file and Poe task to launch the server alongside the official **MCP Inspector** web interface.

### Step 1: Start the Inspector Stack

From your terminal, run:

```bash
uv run poe compose-inspector
```

This command orchestrates two containerized services:
- **`ebook-mcp-server`**: The FastMCP Python server listening for SSE connections on `http://localhost:8000/sse`.
- **`mcp-inspector`**: The Node.js MCP Inspector web UI listening on `http://localhost:6274`.

> **Zero-Configuration Setup**: The `.mcp/mcp.json` file is automatically mounted into the Inspector container (`--config /app/mcp.json`), so `ebook-mcp-server` is pre-connected automatically without requiring manual connection setup.

### Step 2: Open the Web UI

Open your browser and navigate to:

👉 **[http://localhost:6274](http://localhost:6274)**

---

## 3. Exploring the "Tools" Tab in MCP Inspector

Once the Inspector interface loads:

1. Click on the **Tools** tab in the top navigation bar.
2. Click **List Tools**. The Inspector will query `ebook-mcp-server` and display all registered tools alongside their JSON schemas, arguments, and docstrings.

Notice how the AI model sees the tools:
- **`get_all_epub_files`**: Lists all `.epub` e-books in a specified directory path.
- **`get_epub_metadata`**: Extracts metadata (title, author, publisher, language).
- **`get_epub_toc`**: Retrieves the Table of Contents as a list of `(title, href)` entries.
- **`get_epub_chapter_markdown`**: Extracts chapter content formatted in clean Markdown.

---

## 4. Step-by-Step E-Book Discovery Walkthrough

Let's follow a realistic tool chain that an LLM agent uses when exploring e-books.

### Step 1: Discover E-Books (`get_all_epub_files`)

In the **Tools** tab:
1. Select `get_all_epub_files`.
2. Enter the argument:
   ```json
   {
     "path": "/library"
   }
   ```
3. Click **Run Tool**.

**Response**:
```json
[
  "sample_books/alice_in_wonderland.epub"
]
```
The server returns relative paths to all public domain e-books mounted in `/library`.

---

### Step 2: Extract Table of Contents (`get_epub_toc`)

Next, inspect the structure of the discovered e-book:

1. Select `get_epub_toc`.
2. Enter the argument:
   ```json
   {
     "epub_path": "sample_books/alice_in_wonderland.epub"
   }
   ```
3. Click **Run Tool**.

**Response**:
```json
[
  ["Alice’s Adventures in Wonderland", "6260297267691793459_11-h-0.htm.html#pgepubid00000"],
  ["THE MILLENNIUM FULCRUM EDITION 3.0", "6260297267691793459_11-h-0.htm.html#pgepubid00001"],
  ["Contents", "6260297267691793459_11-h-0.htm.html#pgepubid00002"],
  ["CHAPTER I. Down the Rabbit-Hole", "6260297267691793459_11-h-1.htm.html#pgepubid00003"],
  ["CHAPTER II. The Pool of Tears", "6260297267691793459_11-h-2.htm.html#pgepubid00004"],
  ["CHAPTER III. A Caucus-Race and a Long Tale", "6260297267691793459_11-h-3.htm.html#pgepubid00005"]
]
```

Each chapter entry is returned as a `(title, href)` pair.

---

### Step 3: Fetch Chapter Content (`get_epub_chapter_markdown`)

Now, retrieve the complete content of Chapter 2.

`ebook-mcp` implements a **4-tier flexible fallback search** for `chapter_id`, allowing you or an LLM to request chapters using any of the following formats:

1. **Human Chapter Title** (Recommended for LLMs):
   ```json
   {
     "epub_path": "sample_books/alice_in_wonderland.epub",
     "chapter_id": "CHAPTER II. The Pool of Tears"
   }
   ```

2. **Case-Insensitive or Substring Title**:
   ```json
   {
     "epub_path": "sample_books/alice_in_wonderland.epub",
     "chapter_id": "Pool of Tears"
   }
   ```

3. **1-Based Chapter Index**:
   ```json
   {
     "epub_path": "sample_books/alice_in_wonderland.epub",
     "chapter_id": "5"
   }
   ```

4. **Raw Internal EPUB href Link**:
   ```json
   {
     "epub_path": "sample_books/alice_in_wonderland.epub",
     "chapter_id": "6260297267691793459_11-h-2.htm.html#pgepubid00004"
   }
   ```

Select `get_epub_chapter_markdown`, enter any of the above input formats, and click **Run Tool**.

**Response**:
```markdown
# CHAPTER II. The Pool of Tears

“Curiouser and curiouser!” cried Alice (she was so much surprised, that for the moment she quite forgot how to speak good English)...
```

The tool returns formatted Markdown content ready for synthesis, summarization, or study guide generation!

---

## 5. Summary

Using **MCP Inspector**, you can visually verify how LLM agents interact with `ebook-mcp`:
1. Discover files with `get_all_epub_files`.
2. Retrieve chapter listings with `get_epub_toc`.
3. Extract chapter content seamlessly using `get_epub_chapter_markdown` with human-readable titles, indexes, or internal href links.
