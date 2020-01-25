import click

@click.group()
def main():
   pass

@main.command()
@click.argument('services')
# @click.option(
#     '--api-key', '-a',
#     help='your API key for the OpenWeatherMap API',
# )
def start(services):
    print('started!!');

if __name__ == "__main__":
    main()