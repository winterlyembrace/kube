FROM node:25-alpine3.22

WORKDIR /frontend

RUN npx create-react-app . 

RUN npm install axios monaco-editor react-monaco-editor cytoscape react-cytoscapejs 

RUN npm install -D tailwindcss postcss autoprefixer

RUN npx tailwindcss init -p

RUN rm tailwind.config.js
RUN rm src/index.css
RUN rm src/index.js

COPY tailwind.config.js .
COPY src/index.css src/index.css
COPY src/index.js src/index.js

ENV PORT=5000

CMD ["npm", "serve", "-l", "5000"]
