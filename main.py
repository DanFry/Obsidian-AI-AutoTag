import os
import re
import requests
from dotenv import load_dotenv
import time
from colorama import init, Fore, Style
import json

# Initialize colorama for cross-platform colored output
init()

# Load environment variables
load_dotenv()

# Get API key and Obsidian directory from environment variables
claude_api_key = os.getenv('CLAUDE_API_KEY')
obsidian_directory = os.getenv('OBSIDIAN_DIRECTORY')
use_ollama = os.getenv('USE_OLLAMA', 'false').lower() == 'true'
ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')

# Global variables for statistics
start_time = time.time()
api_queries = 0
total_tokens = 0

def scan_directory(directory):
    """
    Recursively scan the given directory for markdown files and process them.
    """
    print(f"{Fore.CYAN}Scanning directory: {directory}{Style.RESET_ALL}")
    processed_files = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('zTemplates', 'cheat-sheets-main', 'zz_Attachments', '00 Monthly Tasks', 'BMO', 'zz_Archive')]
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                result = process_file(file_path)
                processed_files.append(result)
    
    print_statistics(processed_files)

def process_file(file_path, retry_limit=3):
    """
    Process a single markdown file. Check if it has tags, and if not, generate and add them.
    If the generated tags exceed 10, retry up to `retry_limit` times.
    """
    print(f"\n{Fore.BLUE}Processing file: {file_path}{Style.RESET_ALL}")
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    existing_tags = extract_existing_tags(content)
    if len(existing_tags) < 9:
        print(f"{Fore.YELLOW}Less than 9 existing tags found. Generating additional tags...{Style.RESET_ALL}")
        retry_count = 0
        while retry_count < retry_limit:
            suggested_tags = get_suggested_tags(content)
            if suggested_tags:
                if len(suggested_tags) > 10:
                    print(f"{Fore.YELLOW}Warning: Generated more than 10 tags. Retrying...{Style.RESET_ALL}")
                    retry_count += 1
                else:
                    # Combine existing and suggested tags
                    all_tags = existing_tags + [tag for tag in suggested_tags if tag not in existing_tags]
                    # Correct tags to ensure they have '#' symbol
                    corrected_tags = []
                    for tag in all_tags:
                        if not tag.startswith('#'):
                            tag = '#' + tag.strip()
                        corrected_tags.append(tag)
                    # Truncate to 10 tags if necessary
                    corrected_tags = corrected_tags[:10]
                    tag_string = ' '.join(corrected_tags)
                    if re.search(r'\nTags:\s*(.*?)$', content, re.MULTILINE):
                        content = re.sub(r'\nTags:\s*(.*?)$', f"\nTags: {tag_string}", content, flags=re.MULTILINE)
                    else:
                        content += f"\nTags: {tag_string}"
                    with open(file_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    print(f"{Fore.GREEN}Updated tags: {tag_string}{Style.RESET_ALL}")
                    return {"file": file_path, "status": "tags_updated", "tags": corrected_tags}
            else:
                print(f"{Fore.RED}Failed to generate tags.{Style.RESET_ALL}")
                return {"file": file_path, "status": "failed", "tags": []}
        print(f"{Fore.RED}Exceeded retry limit. Skipping file.{Style.RESET_ALL}")
        return {"file": file_path, "status": "failed", "tags": []}
    else:
        print(f"{Fore.CYAN}10 or more existing tags found: {' '.join(existing_tags)}{Style.RESET_ALL}")
        return {"file": file_path, "status": "existing_tags", "tags": existing_tags}

def get_suggested_tags(content):
    """
    Get suggested tags using either Ollama or Claude API.
    """
    if use_ollama:
        return get_suggested_tags_ollama(content)
    else:
        return get_suggested_tags_claude(content)

def get_suggested_tags_ollama(content):
    """
    Send the content to Ollama and get suggested tags.
    """
    global api_queries, total_tokens
    prompt = f"""
You are an AI assistant tasked with generating exactly 9 relevant tags for an Obsidian markdown file. Your goal is to analyze the provided content and suggest 9 distinct tags that comprehensively classify the key topics discussed in the text.

Here is the content you need to analyze:

<content>
{content}
</content>

To complete this task, follow these guidelines:

1. Carefully read and analyze the entire content provided above.
2. Identify the main topics, themes, and key concepts present in the text.
3. Generate exactly 9 distinct tags that best represent the content.
4. Ensure that each tag is relevant to the text and captures an important aspect of the content.
5. Make the tags comprehensive, covering different aspects of the text rather than focusing on a single theme.
6. Each tag should be a single word or a short phrase.
7. Prefix each tag with the '#' symbol.
8. Separate each tag with a single space.

Important notes:
- Focus solely on the content provided.
- Do not provide any explanations, additional text, or formatting beyond the 9 tags.
- Your response should consist of exactly 9 tags, no more and no less.
- If you are not sure include tags based on external knowledge or assumptions.
- Do not include tags related to the Obsidian software (e.g #Obsidian or #Content or #Markdown) Focus on the content.

Your output should look like this:
#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8 #tag9

Provide your response with only the 9 tags, following the format specified above.
"""


    print(f"{Fore.YELLOW}Sending request to Ollama...{Style.RESET_ALL}")
    api_queries += 1
    response = requests.post('http://localhost:11434/api/generate',
                             json={
                                 "model": ollama_model,
                                 "prompt": prompt,
                             })

    if response.status_code == 200:
        try:
            response_lines = response.text.strip().split('\n')
            response_json = json.loads(response_lines[-1])
            response_text = ''.join(json.loads(line)['response'] for line in response_lines)
            tags = response_text.strip().split()
            corrected_tags = []
            for tag in tags:
                tag = tag.strip('# ')
                if not tag.startswith('#'):
                    tag = '#' + tag
                corrected_tags.append(tag)
            total_tokens += response_json.get('total_tokens', 0)
            print(f"{Fore.GREEN}Received tags from Ollama.{Style.RESET_ALL}")
            return corrected_tags
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{Fore.RED}Error decoding JSON response from Ollama: {e}{Style.RESET_ALL}")
            print(f"{Fore.RED}Response content: {response.text}{Style.RESET_ALL}")
            return None
    else:
        print(f"{Fore.RED}Error with Ollama: {response.status_code}, {response.text}{Style.RESET_ALL}")
        return None


def get_suggested_tags_claude(content):
    """
    Send the content to Claude API and get suggested tags.
    """
    global api_queries, total_tokens
    system_prompt = """
    
You are an AI assistant tasked with generating exactly 9 relevant tags for an Obsidian markdown file. Your goal is to analyze the provided content and suggest 9 distinct tags that comprehensively classify the key topics discussed in the text.

Here is the content you need to analyze:

<content>
{content}
</content>

To complete this task, follow these guidelines:

1. Carefully read and analyze the entire content provided above.
2. Identify the main topics, themes, and key concepts present in the text.
3. Generate exactly 9 distinct tags that best represent the content.
4. Ensure that each tag is relevant to the text and captures an important aspect of the content.
5. Make the tags comprehensive, covering different aspects of the text rather than focusing on a single theme.
6. Each tag should be a single word or a short phrase.
7. Prefix each tag with the '#' symbol.
8. Separate each tag with a single space.

Important notes:
- Focus solely on the content provided.
- Do not provide any explanations, additional text, or formatting beyond the 9 tags.
- Your response should consist of exactly 9 tags, no more and no less.
- If you are not sure include tags based on external knowledge or assumptions.
- Do not include tags related to the Obsidian software (e.g #Obsidian or #Content or #Markdown) Focus on the content.

Your output should look like this:
#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8 #tag9

Provide your response with only the 9 tags, following the format specified above.
    """

    print(f"{Fore.YELLOW}Sending request to Claude API...{Style.RESET_ALL}")
    api_queries += 1
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": claude_api_key,
        },
        json={
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
        }
    )

    if response.status_code == 200:
        response_json = response.json()
        tags = response_json['content'][0]['text'].strip().split()
        total_tokens += response_json.get('usage', {}).get('total_tokens', 0)
        print(f"{Fore.GREEN}Received tags from Claude API.{Style.RESET_ALL}")
        return tags
    else:
        print(f"{Fore.RED}Error with Claude API: {response.status_code}, {response.text}{Style.RESET_ALL}")
        return None

def extract_existing_tags(content):
    """
    Extract existing tags from the content.
    """
    match = re.search(r'\nTags:\s*(.*?)$', content, re.MULTILINE)
    if match:
        return [tag.strip() for tag in match.group(1).split('#') if tag.strip()]
    return []

def print_statistics(processed_files):
    """
    Print comprehensive statistics about the processed files and script performance.
    """
    total_files = len(processed_files)
    tags_updated = sum(1 for file in processed_files if file['status'] == 'tags_updated')
    existing_tags = sum(1 for file in processed_files if file['status'] == 'existing_tags')
    failed = sum(1 for file in processed_files if file['status'] == 'failed')
    
    end_time = time.time()
    run_time = end_time - start_time
    
    print(f"\n{Fore.CYAN}=== Run Statistics ==={Style.RESET_ALL}")
    print(f"{Fore.WHITE}Total files processed: {total_files}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Files with tags updated: {tags_updated}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}Files with existing tags: {existing_tags}{Style.RESET_ALL}")
    print(f"{Fore.RED}Files that failed: {failed}{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Performance Statistics:{Style.RESET_ALL}")
    print(f"Total run time: {run_time:.2f} seconds")
    print(f"Average time per file: {run_time/total_files:.2f} seconds")
    print(f"Total API queries: {api_queries}")
    print(f"Total tokens used: {total_tokens}")
    
    if not use_ollama:
        # Estimate cost (assuming $0.08 per 1K tokens for Claude 3)
        estimated_cost = (total_tokens / 1000) * 0.08
        print(f"\n{Fore.YELLOW}Estimated API cost: ${estimated_cost:.2f}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}Using Ollama locally (no API costs){Style.RESET_ALL}")

def main():
    if not obsidian_directory:
        print(f"{Fore.RED}Error: OBSIDIAN_DIRECTORY not set in .env file.{Style.RESET_ALL}")
    elif not use_ollama and not claude_api_key:
        print(f"{Fore.RED}Error: CLAUDE_API_KEY not set in .env file and Ollama is not enabled.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Starting Obsidian Tag Generator{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Using {'Ollama' if use_ollama else 'Claude API'} for tag generation{Style.RESET_ALL}")
        scan_directory(obsidian_directory)
        print(f"\n{Fore.GREEN}Obsidian Tag Generator completed.{Style.RESET_ALL}")

if __name__ == "__main__":
    main()
