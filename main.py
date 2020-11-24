from PIL import Image, ImageFont, ImageDraw
from googletrans import Translator
from io import BytesIO
from os import listdir
import random
import requests
import praw


def make_affirmation(image_url, affirmation_text, path_to_font, text_color, img_fraction=0.5, output_name="affirmation"):
    '''
    Adds some text to an image

        Parameters:

            image_url (string):         url to the image that you want to edit
            affirmation_text (string):  the text that you want to add
            path_to_font (string):      path to the .ttf file of the font you want to use
            text_color (r, g, b):       tuple of rgb values for the text color
            img_fraction (float):       fraction of image width you want text to fill
            output_name (string):       name of output image, .jpg will be appended

        Returns:
            The path of the image you made
    '''
    # Get the image file from the supplied URL and load it in PIL
    response = requests.get(image_url)
    affirmation_image = Image.open(BytesIO(response.content))

    font_size = 1 # initial font size
    affirmation_font = ImageFont.truetype(path_to_font, font_size)

    # find longest line of text
    longest_line = max(affirmation_text.split('\n'), key=len)

    # loop to find the font-size we need to use to fill desired portion of image
    while affirmation_font.getsize(longest_line)[0] < img_fraction*affirmation_image.size[0]:
        font_size += 1
        affirmation_font = ImageFont.truetype(path_to_font, font_size)

    font_size -= 1 # de-increment to make sure where within bounds
    affirmation_font = ImageFont.truetype(path_to_font, font_size)

    # place the text in the middle of the photo
    text_position_x = int((affirmation_image.size[0] / 2) - (affirmation_font.getsize(longest_line)[0] / 2))
    text_position_y = int((affirmation_image.size[1] / 2) - (affirmation_font.getsize(affirmation_text)[1]))

    # Count the number of lines 
    lines_in_text = affirmation_text.count('\n') + 1

    r_x1 = text_position_x - 10
    r_y1 = text_position_y - 5
    r_x2 = r_x1 + affirmation_font.getsize(longest_line)[0] + 10
    r_y2 = r_y1 + affirmation_font.getsize(affirmation_text)[1] * lines_in_text + 10

    # add the text
    image_editable = ImageDraw.Draw(affirmation_image)
    image_editable.rectangle(((r_x1, r_y1), (r_x2, r_y2)), fill=opposite_color(text_color))
    image_editable.text((text_position_x, text_position_y), affirmation_text, text_color, font=affirmation_font, align='center')

    # save the image
    affirmation_image.save(f"{output_name}.jpg")

    return (f"{output_name}.jpg")


def get_quote():
    '''
    Gets a random quote from https://zenquotes.io/api/random and translates it into Norwegian
    '''
    translator = Translator()

    # Get random quote JSON object
    response = requests.get('https://zenquotes.io/api/random')
    json = response.json()[0]

    # Translation API fails sometimes so we want to try up to ten times, if it fails then, keep original
    translated = False
    tries = 0
    quote = ""
    while not translated:
        try:
            translation = translator.translate(json['q'], src='en', dest='no')
            quote = translation.text
            translated = True
        except AttributeError:
            tries += 1
            if tries >= 10:
                quote = json['q']
                break
            
    # if the quote is long, split it at commas or full stops
    if len(quote) > 16:
        if ',' in quote:
            quote = quote.replace(',', ',\n')
        elif '. ' in quote:
            quote = quote.replace('. ', '.\n')

    return(quote, json['a'])


def get_image_url(subreddit):
    """returns a random image url from the 100 hot posts in a given subreddit"""
    # create reddit instance
    reddit = praw.Reddit("Affirmasjoner")

    # get a list of submission urls
    submissions = [s.url for s in reddit.subreddit(subreddit).hot(limit=100)]
    found_url = False

    # get a url that leads to a jpg or png
    while not found_url:
        url = random.choice(submissions)
        if url[-4:] == '.jpg' or url[-4:] == '.png':
            return url


def random_font(fonts):
    """Picks a random font from the supplied list of fonts"""
    return './fonts/' + random.choice(fonts)

def random_color():
    """Returns a random bright RGB color"""
    r = random.randint(64,255)
    g = random.randint(64,255)
    b = random.randint(64,255)
    return (r, g, b)


def opposite_color(color):
    """Inverts the given (r, g, b) color"""
    r = 255 - color[0]
    g = 255 - color[1]
    b = 255 - color[2]
    # r = max(color) + min(color) - color[0]
    # g = max(color) + min(color) - color[1]
    # b = max(color) + min(color) - color[2]
    return (r, g, b)

# Make our font list
font_list = listdir('./fonts')

if __name__ == "__main__":
    make_affirmation(get_image_url("natureporn"), get_quote()[0], random_font(font_list), random_color(), 0.9, "./images/affirmasjon")
