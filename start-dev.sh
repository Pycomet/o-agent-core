#!/bin/bash

echo "Starting Trigger.dev..."
cd trigger
npm install && cd ..
echo "Starting Trigger.dev..."
npx trigger.dev@latest dev &

echo "Building and starting Docker..."
docker-compose up --build &

echo "All services started successfully!"

