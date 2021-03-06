__author__ = "Taavi Päll"
__copyright__ = "Copyright 2020, Taavi Päll"
__email__ = "taavi.pall@ut.ee"
__license__ = "MIT"


from snakemake.shell import shell

extra=snakemake.params.get("extra", "")
log = snakemake.log_fmt_shell(stdout=False, stderr=True)

shell(
    "gatk IndexFeatureFile {extra} -I {snakemake.input[0]} -O {snakemake.output[0]} {log}"
)
