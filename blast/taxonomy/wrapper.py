import pandas as pd
from pkg_resources import parse_version
if parse_version(pd.__version__) < parse_version("0.24.0"):
    print("Warning pandas version is {} and taxon ids will be floating point numbers in results\nand column order is not preserved. To avoid this, please install pandas>=0.24.0.".format(pd.__version__))
from ete3 import NCBITaxa
import numpy as np
import argparse

def split(x, n):
    k, m = divmod(len(x), n)
    return (x[i * k + min(i, m): (i + 1) * k + min(i + 1, m)] for i in range(n))

# Create BLAST BD and query classes
class BlastDB:

    def __init__(self, dbfile=None):
        self.ncbi = NCBITaxa(dbfile=dbfile)
    
    def get_lineage(self, taxid):
        return self.ncbi.get_lineage(taxid)

    def get_rank(self, taxids):
        return self.ncbi.get_rank(taxids)
    
    def get_topology(self, lineage):
        return self.ncbi.get_topology(lineage)

    def get_normalised_lineage(self, taxid, ranks_of_interest, taxonomic_ranks, unidentified):
        # Dictionary that maps taxonomic ranks to integers,
        # the lowest is "no rank": 0
        numeric_rank = {taxonomic_ranks[i]: i for i in range(len(taxonomic_ranks))}
        # Get lineage for taxid and map it to numeric rank
        lineage = self.get_lineage(taxid)
        updated_taxid=[lineage[-1]]
        _, rank_of_query = self.get_rank(updated_taxid).popitem()
        num_rank_of_query = numeric_rank[rank_of_query]
        ranks = self.get_rank(lineage)
        invert_dict = {v: k for k, v in ranks.items()}
        lineage_ranks = invert_dict.keys()
        # Get ranks and taxids
        # if rank is not present in lineage, say is unidentified
        normalised_lineage = dict()
        for rank in ranks_of_interest:
            num_rank_to_get = numeric_rank[rank]
            # must be above taxid in hierarchy
            if num_rank_to_get >= num_rank_of_query:
                if rank in lineage_ranks:
                    normalised_lineage[rank] = invert_dict[rank]
                else:
                    normalised_lineage[rank] = unidentified
        return normalised_lineage

class BlastTaxonomy(BlastDB):
    
    def __init__(self, results, pp_sway=1, ranks_of_interest=None, taxonomic_ranks=None, dbfile=None):
        
        BlastDB.__init__(self, dbfile)
        self.by_query = results.groupby("query") 
        self.pp_sway = pp_sway
        if ranks_of_interest:
            self.ranks_of_interest = ranks_of_interest
        else:
            self.ranks_of_interest = ['superkingdom', 'order', 'family', 'genus', 'species']
        if taxonomic_ranks:
            self.taxonomic_ranks = taxonomic_ranks
        else:
            self.taxonomic_ranks = [ "no rank", "species", "genus", "family", "order", "class", "phylum", "kingdom", "superkingdom"]
        self.unidentified = 32644
    
    def get_consensus_taxonomy(self):
        consensus_taxonomy = []
        for query, hits in self.by_query:
            if hits.shape[0] > 1:
                pident_threshold = hits["pident"].aggregate("max") - self.pp_sway
                within = hits["pident"].apply(lambda x: x >= pident_threshold)
                hits_filtered = hits[within]
                taxlist = hits_filtered["tax_id"].tolist()
                if len(taxlist) > 1:
                    lineage = []
                    for tax in taxlist:
                        normalised_lineage = self.get_normalised_lineage(tax, self.ranks_of_interest, self.taxonomic_ranks, self.unidentified)
                        rev_normalised_lineage = {v: k for k, v in normalised_lineage.items()}
                        lineage.append(set(rev_normalised_lineage))
                    lineage_intersect = list(set.intersection(*lineage))
                    root_tree = self.get_topology(lineage_intersect)
                    consensus = root_tree.get_leaf_names()
                else:
                    consensus = taxlist
            else:
                consensus = hits["tax_id"].tolist()
            con_lin = self.get_normalised_lineage(consensus[0], self.ranks_of_interest, self.taxonomic_ranks, self.unidentified)
            consensus_taxonomy.append(dict({"query": query, "consensus": consensus[0], "pident": hits["pident"].aggregate("max"), "hits": hits.shape[0]}, **con_lin))
        return pd.DataFrame(consensus_taxonomy)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Process BLAST+ taxonomy in chunks.")
    parser.add_argument("--infile", dest = "filename", type = argparse.FileType("r"), 
                    required=True,
                    help = "Path to input file with BLAST results")
    parser.add_argument("-i", dest = "index", type = int, nargs = 1,
                        required=True,
                    help = "Array index, an integer")
    parser.add_argument("-s", dest = "size", type = int, nargs = 1,
                    required = True, help = "Array size, an integer")
    parser.add_argument("--nrows", dest = "nrows", default = None,
                        help = "Number of rows of file to read. Useful for reading pieces of large files.")
    args = parser.parse_args()

    # Output file prefix
    out_prefix = "consensus_taxonomy"
    
    # Import file with BLAST results
    results = pd.read_csv(args.filename, index_col = "query", nrows = int(args.nrows) if args.nrows else args.nrows)[["gi", "pident", "evalue", "tax_id"]]
    
    # Get query indices
    by_query = results.groupby("query")
    queries = [*by_query.indices]

    # Split queries into n chunks
    query_chunks = list(split(queries, args.size[0]))

    # Process one chunk
    queries_to_process = query_chunks[args.index[0] - 1]
    bt = BlastTaxonomy(results.loc[queries_to_process])
    consensus_taxonomy = bt.get_consensus_taxonomy()
    consensus_taxonomy[["superkingdom", "order", "family", "genus", "species"]] = consensus_taxonomy[["superkingdom", "order", "family", "genus", "species"]].apply(lambda x: pd.Series(x, dtype="Int64"))
    consensus_taxonomy.to_csv("{}_{}.csv".format(out_prefix, args.index[0]), index = False)
