local: ##@Develop Run dev containers for test
	docker compose -f docker-compose.dev.yaml up --force-recreate --renew-anon-volumes --build

local-down: ##@Develop Stop dev containers with delete volumes
	docker compose -f docker-compose.dev.yaml down -v
