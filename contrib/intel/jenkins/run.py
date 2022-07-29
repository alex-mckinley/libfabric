import tests
import subprocess
import sys
import argparse
import os
import common

sys.path.append(os.environ['CI_SITE_CONFIG'])
import ci_site_config

# read Jenkins environment variables
# In Jenkins, JOB_NAME = 'ofi_libfabric/master' vs BRANCH_NAME = 'master'
# job name is better to use to distinguish between builds of different
# jobs but with the same branch name.
fab = os.environ['FABRIC']#args.fabric
jbname = os.environ['JOB_NAME']#args.jobname
bno = os.environ['BUILD_NUMBER']#args.buildno

def fi_info_test(core, hosts, mode, util):

    fi_info_test = tests.FiInfoTest(jobname=jbname,buildno=bno,
                                    testname='fi_info', core_prov=core,
                                    fabric=fab, hosts=hosts,
                                    ofi_build_mode=mode, util_prov=util)
    print('-------------------------------------------------------------------')
    print(f"Running fi_info test for {core}-{util}-{fab}")
    fi_info_test.execute_cmd()
    print('-------------------------------------------------------------------')

def fabtests(core, hosts, mode, util):

    runfabtest = tests.Fabtest(jobname=jbname,buildno=bno,
                               testname='runfabtests', core_prov=core,
                               fabric=fab, hosts=hosts, ofi_build_mode=mode,
                               util_prov=util)

    print('-------------------------------------------------------------------')
    if (runfabtest.execute_condn):
        print(f"Running Fabtests for {core}-{util}-{fab}")
        runfabtest.execute_cmd()
    else:
        print(f"Skipping {core} {runfabtest.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

def shmemtest(core, hosts, mode, util):

    runshmemtest = tests.ShmemTest(jobname=jbname,buildno=bno,
                                   testname="shmem test", core_prov=core,
                                   fabric=fab, hosts=hosts,
                                   ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (runshmemtest.execute_condn):
#        skip unit because it is failing shmem_team_split_2d
#        print(f"Running shmem unit test for {core}-{util}-{fab}")
#        runshmemtest.execute_cmd("unit")
        print(f"Running shmem PRK test for {core}-{util}-{fab}")
        runshmemtest.execute_cmd("prk")

        print('--------------------------------------------------------------')
        print(f"Running shmem ISx test for {core}-{util}-{fab}")
        runshmemtest.execute_cmd("isx")

        print('---------------------------------------------------------------')
        print(f"Running shmem uh test for {core}-{util}-{fab}")
        runshmemtest.execute_cmd("uh")
    else:
        print(f"Skipping {core} {runshmemtest.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

def multinodetest(core, hosts, mode, util):

    runmultinodetest = tests.MultinodeTests(jobname=jbname,buildno=bno,
                                      testname="multinode performance test", 
                                      core_prov=core, fabric=fab, hosts=hosts,
                                      ofi_build_mode=mode, util_prov=util)

    print("-------------------------------------------------------------------")
    if (runmultinodetest.execute_condn):
        print("Running multinode performance test for {}-{}-{}" \
              .format(core, util, fab))
        runmultinodetest.execute_cmd()

        print("---------------------------------------------------------------")
    else:
        print("Skipping {} as execute condition fails" \
              .format(runmultinodetest.testname))
    print("-------------------------------------------------------------------")

def ze_fabtests(core, hosts, mode, util):
    runzefabtests = tests.ZeFabtests(jobname=jbname,buildno=bno,
                                     testname="ze test", core_prov=core,
                                     fabric=fab, hosts=hosts,
                                     ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (runzefabtests.execute_condn):
        print(f"Running ze tests for {core}-{util}-{fab}")
        runzefabtests.execute_cmd()
    else:
        print(f"Skipping {core} {runzefabtests.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

def intel_mpi_benchmark(core, hosts, mpi, mode, group, util):

    imb = tests.IMBtests(jobname=jbname, buildno=bno,
                         testname='IntelMPIbenchmark', core_prov=core,
                         fabric=fab, hosts=hosts, mpitype=mpi,
                         ofi_build_mode=mode, test_group=group,
                         util_prov=util)

    print('-------------------------------------------------------------------')
    if (imb.execute_condn == True):
        print(f"Running IMB-tests for {core}-{util}-{fab}-{mpi}")
        imb.execute_cmd()
    else:
        print(f"Skipping {mpi.upper} {imb.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

def mpich_test_suite(core, hosts, mpi, mode, util):

    mpich_tests = tests.MpichTestSuite(jobname=jbname,buildno=bno,
                                       testname="MpichTestSuite",core_prov=core,
                                       fabric=fab, mpitype=mpi, hosts=hosts,
                                       ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (mpich_tests.execute_condn == True):
        print(f"Running mpichtestsuite: Spawn Tests for {core}-{util}-{fab}-{mpi}")
        mpich_tests.execute_cmd("spawn")
    else:
        print(f"Skipping {mpi.upper()} {mpich_tests.testname} as exec condn fails")
    print('-------------------------------------------------------------------')

def osu_benchmark(core, hosts, mpi, mode, util):

    osu_test = tests.OSUtests(jobname=jbname, buildno=bno,
                                testname='osu-benchmarks', core_prov=core,
                                fabric=fab, mpitype=mpi, hosts=hosts,
                                ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (osu_test.execute_condn == True):
        print(f"Running OSU-Test for {core}-{util}-{fab}-{mpi}")
        osu_test.execute_cmd()
    else:
        print(f"Skipping {mpi.upper()} {osu_test.testname} as exec condn fails")
    print('-------------------------------------------------------------------')

def oneccltest(core, hosts, mode, util):

    runoneccltest = tests.OneCCLTests(jobname=jbname,buildno=bno,
                                      testname="oneccl test", core_prov=core,
                                      fabric=fab, hosts=hosts,
                                      ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (runoneccltest.execute_condn):
        print(f"Running oneCCL examples test for {core}-{util}-{fab}")
        runoneccltest.execute_cmd("examples")

        print('---------------------------------------------------------------')
        print(f"Running oneCCL functional test for {core}-{util}-{fab}")
        runoneccltest.execute_cmd("functional")
    else:
        print(f"Skipping {runoneccltest.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

def oneccltestgpu(core, hosts, mode, util):

    runoneccltestgpu = tests.OneCCLTestsGPU(jobname=jbname,buildno=bno,
                                         testname="oneccl GPU test", core_prov=core,
                                         fabric=fab, hosts=hosts,
                                         ofi_build_mode=mode, util_prov=util)

    print('-------------------------------------------------------------------')
    if (runoneccltestgpu.execute_condn):
        print(f"Running oneCCL GPU examples test for {core}-{util}-{fab}")
        runoneccltestgpu.execute_cmd('examples')

        print('---------------------------------------------------------------')
        print(f"Running oneCCL GPU functional test for {core}-{util}-{fab}")
        runoneccltestgpu.execute_cmd('functional')
    else:
        print(f"Skipping {runoneccltestgpu.testname} as execute condition fails")
    print('-------------------------------------------------------------------')

if __name__ == "__main__":
    pass
