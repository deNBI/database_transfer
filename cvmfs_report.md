# Evaluating the possible usage of CVM-FS for the distribution of large biological data

A good introduction and explanation can be found 
[here](https://cvmfs.readthedocs.io/en/2.5/index.html).
This report contains first results of using the *CernVM-FS* (short *cvmfs*) for *denbi* 
to distribute large biological datasets. The data used can be found 
[here](https://openstack.cebitec.uni-bielefeld.de:8080/blast) within a Swift bucket.

## Goals

- Speed comparisons of direct downloads (`curl`,...) vs distribution via *cvmfs*
- Collections of setup scripts to lower the barrier of entry of future researchers

## Setup

One strong advantage of *cvmfs* is its caching layer but for this test and like other 
[Large-Scale Data CernVM-FS](https://cvmfs.readthedocs.io/en/2.5/cpt-large-scale.html) 
only a *Stratum 0* repository (single source of data and physically located in the 
Bielefeld Openstack setup) and multiple clients (in Bielefeld and Tübingen) have been 
used.

### Stratum 0

- *de.NBI.medium* Flavour with 1 TB of storage
- accessible from the outside (at least Port 80 for HTTP)

- The [Getting Started](https://cvmfs.readthedocs.io/en/2.5/cpt-quickstart.html) and 
[Creating a Repository (Stratum 0)](https://cvmfs.readthedocs.io/en/2.5/cpt-repo.html) 
pages are sufficient as well as highly recommended

### Client Setup

- *Ansible* has been used to setup the clients. The playbook can be found 
[here](https://github.com/deNBI/database_transfer/tree/cvmfs_client_ansible). Besides 
enabling access to the stratum 0 repository it also replays itself every 10 minutes to 
apply any changes pushed to the git repository.

It also contains a 
[script](https://github.com/deNBI/database_transfer/blob/cvmfs_client_ansible/client_user_data.sh) 
to install `ansible` automatically.

## Tests

Typically `cvmfs` is also used to distribute the data which have been added to a 
`repository` during `transaction` phase. Per default once `cvmfs_server <repo> publish` 
is called the data are
[processed](https://cvmfs.readthedocs.io/en/2.5/cpt-repo.html#publishing-a-new-repository-revision) 
and made available to the clients afterwards. For the distribution a standard Apache 
HTTP server is used since all communication between cvmfs machines is performed via 
HTTP.

The script used to measure the transfer speed is also part of the ansible client 
repository. On the client side the command
`shopt -s globstar; for i in **/*; do cat $i >> /dev/null; done` was used to initiate 
the download of all files and to prevent any bad storage performance to influence the 
results. For repeated tests `cvmfs_config wipecache` was used to empty the cache.

### No external data storage

- In this scenario the clients download the compressed hash-named files from the source 
(typically a cache layer of stratum 1 machines, but in this case no proxy has been used)
- The client was in the same internal network as the stratum 0, a direkt `curl` revealed 
average speeds around 1 GB/s, the results can be found at
`results/base_speed{client,stratum0}.csv`

On the stratum 0 machine the repository was created with the `-Z none` option to disable 
the compression, yet it took multiple hours to process 7.5 GB of data which were added 
to the repository. The following transfer speed measurements showed an average of 33 
MB/s. In hindsight this huge decrease in speed might be caused by not changing the 
default chunk size on the stratum 0 machine. The results can be found at
`results/cvmfs_1-client_7-5-GB_{client,stratum0}.csv`.

### External data storage

As linked in the [Setup] Section, `cvmfs` offers the possibility to specify an external 
url where data are stored, the corresponding repository was created by the following 
command `cvmfs_server mkfs -Z none -X test_ext.datatransfer.bi`. In this mode `cvmfs` 
does not deliver the files itself but only the publication data, which are created by a 
process called 
[`grafting`](https://cvmfs.readthedocs.io/en/2.5/cpt-repo.html#grafting-files). Since 
the bucket containing the data is already accessible via HTTP(S) it could easily be used 
as external source. The following script was used to parallelize the grafting process:

```bash
#!/bin/bash 
 
# assuming that the correct openstack project env vars are set 
 
swift_container='blast' 
 
graft_file() { 
        mkdir -p "$(dirname "${1}")" 
        python3-swift download blast "${1}" -o - | cvmfs_swissknife graft -i - -v -o "${1}" 
} 
 
export -f graft_file 
 
python3-swift list "${swift_container}" | parallel --verbose graft_file
```

- The repository directory structure must mirror the one of the external source since 
the files are now accessed by their name/path.
-`https://github.com/cvmfs/cvmfs/blob/1988d54e0cf363bb5c4cf78cc50b740ec9463235/cvmfs/download.cc#L959` 
shows how to configure `cvmfs` where to look for valid certificates, but despite the 
environment variable `X509_CERT_DIR` having the value `/etc/ssl/certs` any `HTTPS` 
connection failed (curl error 60). A symlink pointing from 
`/etc/grid-security/certificates` to `/etc/ssl/certs` was necessary to circumvent this 
error (this is, most certainly, no error of `cvmfs` but rather a user error).

#### Bielefeld

A direct download via `curl` from the swift bucket from inside the Bielefeld Openstack 
setup showed average download speeds of ~60 MB/s, the test via `cvmfs` showed average 
transfer speeds of ~48MB, the results can be found at
`results/swift_external_all_1-client.csv`.

#### Tübingen

- `curl` shows an average speed of ~23 MB/s
- a download via `cvmfs` shows an average of ~18MB/s, the results can be found at 
`results/test_tuebingen_client_complete.csv`
  - During the transfer 27 `Input/Output` errors were reported indicating that `curl` 
  was not able to download the corresponding from swift

## Possible Future Tasks

- Finding a good chunk size to speed up the direct usage of `cvmfs` without external 
data source
- Determining the source of errors during the download from Tübingen
- Exploring the possibilities [Client 
Plugins](https://cvmfs.readthedocs.io/en/2.5/cpt-plugins.html)
- contacting the `opensciencegrid` project since they are already maintaining a 
repository with up to 3 PB
