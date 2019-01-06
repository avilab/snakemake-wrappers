__author__ = "Taavi Päll"
__copyright__ = "Copyright 2018, Taavi Päll"
__email__ = "tapa741@gmail.com"
__license__ = "MIT"

from snakemake.shell import shell

# Get parameters
seed = snakemake.params.get("seed", "11")
print("This is seed:", seed)
frac = snakemake.params.get("frac", "1")
print("This is frac:", frac)

# Command to run
if (frac > 0 and frac < 1):
    cmd = "seqtk sample -s{{seed}} {{snakemake.input[{i}]}} {{frac}} > {{snakemake.output[{i}]}}"
else:
    cmd = "ln -sr {{snakemake.input[{i}]}} {{snakemake.output[{i}]}}"

# Run command
for index, input in enumerate(snakemake.input):
    cmd = cmd.format(i = index)
    print("This is command:\n", cmd)
    shell(cmd)
