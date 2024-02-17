# Alphafold_serverless
Running Alphafold_MSA over the serverless GPU hosted on runpod

To run a job

Copy env.sample file to .env.sample

Generate an API_KEY and fill the correspoonding field in .env.sample


On runpod, create an endpoint.


Run the command:

```
python3 launch.py  --endpointId endpointId   --msa msa.fasta --output structure.pdb
```
