# Idea History AI Agent

## Motivation
The world is really, really complicated. We often accept the values and ideas of our society as givens - as if they've always existed in their current form. 

But how did we get here? Ideas and values are dynamic, evolving differently across both space and time. Different cultures can hold radically different interpretations of the same concept, and these interpretations themselves change as societies develop and interact.

This project is an attempt to shed some light on how we got where we are now, using AI to trace and record the evolution of different concepts through a directed acyclic graph (DAG). 

Using a DAG to model the evolution of abstract ideas is obviously a **massive** simplification of how cultural and intellectual change actually happens. Hopefully this is a fun/useful starting point though.

The technical goal here was to implement an AI agent from scratch, but my broader aim is to create a tool that helps us better understand our own worldviews (and hopefully question them :)).


## Demo

https://github.com/user-attachments/assets/95860010-e51c-4042-a9f4-0478c5530268



## Setting up
`git clone git@github.com:awiteckzb/idea-history-agent.git`

`cd idea-history-agent`

`python -m venv .venv`

`source .venv/bin/activate`

`pip install -r requirements.txt`

Copy the `.env.example` file to `.env` and fill in the values. You can get the relevant keys from [OpenAI](https://platform.openai.com/), [Anthropic](https://docs.anthropic.com/en/docs/get-started/create-an-api-key), and [Google Programmable Search Engine](https://programmablesearchengine.google.com/). You don't need both OpenAI and Anthropic keys, but you need at least one (just make sure the code in `app/api/main.py` reflects this).

`cp .env.example .env`

### In terminal 1:
`cd backend`

Run the backend:
`python run.py`

### In terminal 2:
`cd frontend`

Install the dependencies for the frontend:
`npm install`

Run the frontend:
`npm run dev`






## Further improvements

### More sophisticated agentic workflow
In my experiments, this current implementation doensn't seem to be that much of an improvement over just asking a powerful model like GPT-4 to generate the history in one call. I think a workflow like this would be more useful and an improvement over the current implementation:

* Have a planning model (a powerful one, e.g. GPT-4o) which generates a plan for the history of the idea. Lay out the different "eras" of the idea (e.g. "1882: Nietzsche proposes the idea of Nihilism", "1914:..."). Then break this down into a series of  `research_task`s. 
* Spawn a bunch of smaller agents, each of which handles a `research_task` and generates nodes in the DAG. 
* Have a specialized edge generation model which takes nodes and generates a list of edges between them (this is the tricky part IMO... establishing a concrete causality/connection between two ideas is tricky and finding sources for this seems difficult).

There are a bunch of other more sophisticated agentic workflows out there but I think this is a good starting point. This [article](https://www.anthropic.com/research/building-effective-agents) by Anthropic is a good overview of the different agentic workflow approaches. 

### Better prompting + context management
The way I manage context in this project is not bad at all. The agent's internal `graph` state gets pretty large even after just a few nodes and edges are added — I found that inputting this entire graph into the LLM was a bit too much, so using a function like `_format_graph_for_llm` to format the graph for the LLM was a decent solution (e.g., we don't include the sources in the formatted graph). 

But I think there's a lot of room for improvement here. To start, I think a nicer way to take the relationship between nodes and edges into account would be a great improvement. Right now I just list the basic information about each node and edge in a linear fashion. 


### Better search engine implementation
Right now I just have a Wikipedia and Google search client, and the search method is pretty basic. I think this largely comes down to the query formulation procedure actually. Having a more concrete workflow for how we generate queries (e.g. start with really broad queries and then get progressively more specific as we get more information) would be a good improvement.

Also, I'd argue that while a more sophisticated search engine would be great, we can harness LLMs as independent researchers much more than we currently do. Right now, the LLMs generate research queries and we use non-AI techniques to find relevant sources — a future implementation could try to use LLMs to construct their own narrative for an idea and then find relevant sources to support their narrative (rather than gathering sources and then constructing the narrative). Basically, just use entirely LLMs to construct the DAG out of the gate and then fill in each node/edge with sources. 

### Frontend lol
Not much else to say here
