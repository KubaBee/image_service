# How to set up this project? 

In order to set up a project follow the steps below:

1. Run 'docker-compose build' -> build the docker image
2. Run 'docker-compose up -d' -> start the defined services (detached mode)
3. Run 'docker-compose exec web /bin/bash' -> run bash inside running container
4. Run 'chmod +x create_group.sh' -> make the script responsible for creating three basic groups executable
5. Run './create_group.sh' -> execute script, it will create Basic, Premium and Enterprise groups
