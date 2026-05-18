# RAG Skill

## Purpose
Retrieve relevant memory or documents and ground agent decisions in available context.

## Usage Conditions
Use when prior runs, decisions, project docs, or external documents can improve accuracy.

## Input Format
- Query
- Memory scope
- Retrieval limit
- Required evidence type

## Execution Steps
1. Search short-term and long-term memory.
2. Retrieve relevant artifacts or document snippets.
3. Summarize only evidence useful to the current task.
4. Preserve source identifiers.

## Output Schema
- query
- results
- source_ids
- summary
- confidence

## Quality Checks
- Retrieved context is relevant.
- Summaries do not invent facts beyond retrieved evidence.

## Failure Handling
If retrieval is empty, continue with explicit no-memory-found context.
