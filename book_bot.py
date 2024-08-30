#Book Bot

#TODO
# Add GPT with list of books you like to filter the books
# Add more sources, like reddit books, goodreads?, amazon etc.

from pynytimes import NYTAPI
import os
import pprint
import json
import re
import html
import requests
import asyncio
from telegram import Bot, InputMediaPhoto
from io import BytesIO
from dotenv import load_dotenv

project_folder = os.path.expanduser('~/Documents')
load_dotenv(os.path.join(project_folder, '.env'))

NYT_API_KEY = os.environ['NYT_API_KEY']
BOOK_BOT_TOKEN = os.environ['BOOK_BOT_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

bot = Bot(token=BOOK_BOT_TOKEN)

def get_nyt_bestsellers():
	book_categories = ["combined-print-and-e-book-nonfiction", "combined-print-and-e-book-fiction", "hardcover-graphic-books", "combined-print-fiction", "celebrities"]
	nyt = NYTAPI(NYT_API_KEY, parse_dates=True)
	all_books = []

	for book_category in book_categories:
		# print("Finding books in: ", book_category)
		best_sellers = nyt.best_sellers_list(name=book_category, date=None)
		books = [{
					"title": book["title"], 
					"author": book["author"],
					"book_image": book["book_image"],
					"amazon_product_url": book["amazon_product_url"],
					"weeks_on_list": book["weeks_on_list"],
					"description": book["description"],
					"isbn10": book["primary_isbn10"]
					} for book in best_sellers]
		all_books += books
	pprint.pp(all_books)
	return all_books

def format_message_into_parts(collection):
	max_length = 4096
	curr_length = 0
	parts = []
	curr_part = ""
	for item in collection:
		item_string = str(item)
		item_string_length = len(item_string)
		if curr_length + item_string_length + 1 < max_length:
			curr_part += item_string + "\n"
			curr_length += item_string_length
		else:
			parts.append(curr_part)
			curr_part = ""
			curr_length = 0
	return parts

def format_message(collections):
	messages = []
	for best_seller in collections:
		message = f"{best_seller["author"]}\n{best_seller["title"]}\n\n{best_seller["description"]}\n{best_seller["amazon_product_url"]}\n\n{best_seller["book_image"]}\n"
		messages.append(message)
	final_message = str("\n".join(messages))
	# print (final_message)
	return final_message

def escape_selected_characters(input_string, characters_to_escape):
    # Create a regex pattern to match any of the characters to escape
    pattern = f"[{re.escape(characters_to_escape)}]"
    
    # Replace each matched character with its escaped version
    escaped_string = re.sub(pattern, lambda x: f"\\{x.group(0)}", input_string)
    
    return escaped_string

def format_message_markdown(collections):
	messages = []
	for best_seller in collections:
		message = f"*{best_seller['title']}*\n" \
                  f"{best_seller['author']}\n\n" \
                  f"{best_seller['description']}\n\n" \
                  f"[View on Amazon]({best_seller['amazon_product_url']})\n\n" \
                  # f"[]({best_seller['book_image']})Some text.\n"
		messages.append(message)
	final_message = str("\n".join(messages))
	characters = "#-"
	return escape_selected_characters(final_message, characters)

def format_message_html(collections):
	messages = []
	for best_seller in collections:
		message = f"<a href={best_seller['book_image']}>&#8205;</a>"
				  # f"<b>{best_seller['title']}</b>\n" \
                  # f"<b>{best_seller['author']}</b>\n\n" \
                  # f"<b>Description:</b> {best_seller['description']}\n\n" \
                  # f"[View on Amazon]({best_seller['amazon_product_url']})\n\n" \
                  # f"![Book Image]({best_seller['book_image']})\n"
		messages.append(message)
	final_message = str("\n".join(messages))
	return html.escape(final_message)

def download_image(url):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        return response.raw
    else:
        raise Exception("Image couldn't be retrieved")

def send_telegram_message(data, format):
	match format:
		case "HTML":
			message = format_message_html(data)
		case "Markdown":
			message = format_message_markdown(data)
		case _:
			message = format_message(data)

	url = f"https://api.telegram.org/bot{BOOK_BOT_TOKEN}/sendMessage"
	payload = {
	    "chat_id": CHAT_ID,
	    "text": message,
	    "parse_mode": format
	}
	response = requests.post(url, data=payload)

	if response.status_code != 200:
	    print("Failed to send message.")
	    print(response.reason)
	    print(response.text)

def split_into_chunks(array, chunk_size):
    if chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer.")
    return [array[i:i + chunk_size] for i in range(0, len(array), chunk_size)]

async def send_book_images(best_sellers):
	images=[]
	for best_seller in best_sellers:
		image_stream = await asyncio.get_running_loop().run_in_executor(None, download_image, best_seller['book_image'])
		media = InputMediaPhoto(media=image_stream, caption=f"https://www.goodreads.com/search?q={best_seller['isbn10']}")
		images.append(media)

	images_in_chunks = split_into_chunks(images, 10)
	for images_chunk in images_in_chunks:
		await bot.send_media_group(chat_id=CHAT_ID, media=images_chunk)


async def main():
	best_sellers = get_nyt_bestsellers();
	# send_telegram_message(best_sellers, "Images")
	# await send_book_images(best_sellers)

if __name__ == '__main__':
    asyncio.run(main())





