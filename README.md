# Obsidian-AI-AutoTag
Local (ollama) or Anthropic (Claude API) based Automatic Content Tagger for Obsidian markdown files

Obsidian-AI-AutoTag is a Python script that automatically generates and adds relevant tags to your Obsidian markdown files using AI. It leverages either the Claude API or Ollama (a local AI model) to analyze the content of your files and suggest appropriate tags.

## Features

- Recursively scans a specified Obsidian directory for markdown files
- Analyzes the content of each file using AI (Claude API or Ollama)
- Generates and adds relevant tags to files with less than 10 existing tags
- Retries tag generation if the suggested tags exceed 10
- Provides comprehensive statistics about the processed files and script performance

## Prerequisites

- Python 3.6 or higher
- An API key for the Claude API (if using Claude instead of Ollama)
- Ollama installed and running locally (if using Ollama instead of Claude)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Obsidian-AI-AutoTag.git
   ```

2. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project directory and provide the necessary configuration:
   ```
   CLAUDE_API_KEY=your_claude_api_key
   OBSIDIAN_DIRECTORY=path/to/your/obsidian/directory
   USE_OLLAMA=false
   OLLAMA_MODEL=llama2
   ```
   - Set `CLAUDE_API_KEY` to your Claude API key if using Claude.
   - Set `OBSIDIAN_DIRECTORY` to the path of your Obsidian directory.
   - Set `USE_OLLAMA` to `true` if you want to use Ollama instead of Claude.
   - Set `OLLAMA_MODEL` to the desired Ollama model (default is 'llama2').

4. If using Ollama, make sure it is installed and running locally on the default port (11434).

## Usage

1. Run the script:
   ```
   python main.py
   ```

2. The script will scan the specified Obsidian directory and process each markdown file.

3. For files with less than 10 existing tags, the script will generate and add relevant tags using the selected AI (Claude or Ollama).

4. After processing all files, the script will display comprehensive statistics about the processed files and script performance.

## Customization

- You can customize the directories to exclude from scanning by modifying the `dirs[:]` list comprehension in the `scan_directory` function.

- If you want to use a different Claude model, update the model name in the `get_suggested_tags_claude` function.

- Adjust the retry limit for tag generation by modifying the `retry_limit` parameter in the `process_file` function.

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## Acknowledgements

- [Claude API](https://www.anthropic.com) for providing the AI tag generation capabilities.
- [Ollama](https://github.com/OllieTheCoder/ollama) for the local AI model option.
