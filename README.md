# Discord League of Legends Team Maker Bot

This is a Discord bot that helps create teams for League of Legends based on the players' rankings. The bot allows users to register their League of Legends summoner name and participate in team formation.

## Features

- Registering and associating a League of Legends summoner name with a Discord user.
- Displaying the list of players ready to play.
- Adding players to the playing list.
- Closing the lobby and forming balanced teams.
- Sending the balanced teams and player ranks to the Discord channel.

## Setup

1. Clone the repository or download the source code files.
2. Install the required dependencies using pipenv:
```shell
pipenv install
```
3. Create a new Discord bot and obtain its token. You can create a bot and get the token from the Discord Developer Portal.
4. Create a new file named `.env` in the root directory and add the following line:
```shell
TOKEN=<your_discord_bot_token>
```
Replace `<your_discord_bot_token>` with the token obtained in step 3.
5. Run the bot by executing the following command using pipenv:
```shell
pipenv run start
```

## Usage

Once the bot is running and connected to your Discord server, you can use the following commands to interact with it:

- `!ping`: Check if the bot is responsive.
- `!reset`: Clear the playing list.
- `!playlist`: Display the list of players ready to play.
- `!register <summoner_name>`: Register your League of Legends summoner name.
- `!play`: Add yourself to the playing list.
- `!close`: Close the lobby and form balanced teams.

## Folder Structure

The code is organized into the following files and folders:

- `main.py`: The entry point of the application. It initializes the Discord bot and runs it.
- `bot/`: A package containing the bot-related modules and files.
- `consts.py`: Constant values used by the bot.
- `db_utils.py`: Database utility functions for loading and registering players.
- `helpers.py`: Helper functions for balancing teams and beautifying team output.
- `data/`: The folder where the bot's data is stored.
- `db.json`: The JSON file used as a simple database for storing player information.
- `Pipfile`: The Pipenv file specifying the project dependencies.

## Contributing

Contributions to the project are welcome. If you find any issues or want to add new features, feel free to submit a pull request.

Please ensure that your code follows the existing style and conventions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more information.
