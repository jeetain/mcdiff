"""Script to plot histogram of xyz coords
AG, August 13, 2012"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from functionshistogram import read_coor
from functionsdiffusion import fit_sqrt_vs_time


def plotsettings():
    plt.rc(('xtick','ytick','axes'), labelsize=24.0)
    plt.rcParams['lines.linewidth'] = 2
    plt.rcParams['axes.linewidth'] = 2
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['xtick.major.size'] = 10
    plt.rcParams['xtick.minor.size'] = 4
    plt.rcParams['xtick.major.size'] = 10
    plt.rcParams['figure.subplot.left']=0.15
    plt.rcParams['figure.subplot.bottom']=0.14
    plt.rcParams['legend.fontsize'] = 18
def plotsettingsax(ax):
    for line in ax.xaxis.get_ticklines() + ax.yaxis.get_ticklines():
        #line.set_color('green')
        line.set_markersize(10)
        line.set_markeredgewidth(2) 
plotsettings()


#=====================
# notations
# dtc  --  time interval (in ps) between saved coordinates
# nstep -- only fit the first nstep time steps
#=====================


##### EXTRA #####
def store_msd(t,msd,filename,error=None):
    assert len(t) == len(msd)
    if error is None:
        error = np.zeros(msd.shape)
    else:
        assert len(t) == len(error)
    f = open(filename,"w+")
    for t1,msd1,error1 in zip(t,msd,error):
        print >> f, t1, msd1, error1
    f.close()


#=====================
# ANALYZE
#=====================

def analyze_dist_1D(list_x,nstep,outdir,dtc):
    """Take the average over the D estimates in each of these x-arrays"""
    # fit range = [0,nstep*dtc[
    assert len(list_x) > 0
    nfiles = len(list_x)
    t = np.arange(0,nstep*dtc,dtc)

    alldist2 = np.zeros((nstep,nfiles),float)
    allD = np.zeros((nfiles),float)

    print "="*5
    print "Results"
    print "making %i fits" %nfiles
    print "fit from %i steps, i.e. time %f ps, actually time %f ps" %(nstep,nstep*dtc,(nstep-1)*dtc)
    for i in range(nfiles):
        dist2 = calc_dist_1D(np.array(list_x[i]))
        # only fit the first nstep time steps (use all atoms)
        average = np.mean(dist2[:nstep,:],1)  # average over the atoms
        alldist2[:,i] = average

        p = np.polyfit(t,average,1)
        allD[i] = p[0]   # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
        # if I want many figures:
        #fit_sqrt_vs_time(np.mean(dist_xy,1),dtc,outdir+"/fig_dist.xy.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_z,1), dtc,outdir+"/fig_dist.z.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_r,1), dtc,outdir+"/fig_dist.r.%i.png"%i,title=str(i))

    # extra figures
    m2 = np.mean(alldist2,axis=1)
    #s2 = np.std(alldist2,axis=1)
    fit_sqrt_vs_time(np.sqrt(m2),dtc,outdir+"/fig_dist.average.png",title="average of %i"%nfiles)

    print_output_D_ave_1D(allD)


def analyze_dist(list_x,list_y,list_z,dn1,outdir,dtc,dn2=None,ddn=1,unitcell=None):
    "Take the average over the D estimates in each of these xyz trajectories"""
    assert len(list_x) > 0
    assert len(list_x) == len(list_y)
    assert len(list_x) == len(list_z)
    nfiles = len(list_x)
    """Conditional Mean Square Distance
    dn1  --  start shift
    dn2  --  end shift
    ddn  --  range(dn1,dn2,ddn)

    Example
      dn1=3, dn2=7, ddn=2
      then dns=[3,5,7], nlags=3, ntime should be 8 or more
    """
    if dn2 is None:
        dn2 = dn1
    assert dn2 >= dn1
    assert ddn >= 1
    lt1 = dn1*dtc
    lt2 = dn2*dtc  # I will fit in region lagtime1 to lagtime2
    dns = np.arange(dn1,dn2+1,ddn)
    lagtimes = dns*dtc
    nlags = len(lagtimes)

    ntime = list_x[0].shape[0]
    natom = list_x[0].shape[1]
    if dns[-1]>=ntime:
        raise ValueError("asking for too many shifts, max dn > ntime: %i,%i"%(dns[-1],ntime))

    #if nstep: lagtimes = np.arange(0,nstep*dtc,dtc)

    alldist2 = np.zeros((nlags,nfiles,3),float)
    allD = np.zeros((nfiles,3),float)

    print "="*5
    print "Results"
    print "making %i fits" %nfiles, "(number of trajectories)"
    print "fit from %i lagtimes, i.e. time %f ps to time %f ps, actually time %f ps" %(
             nlags,lagtimes[0],lagtimes[-1],(dn2-dn1)*dtc)
    print "calculating..."
    for i in range(nfiles):
        print "file",i
        if unitcell is None:
            dist2_xy,dist2_z,dist2_r,weight = calc_dist(list_x[i],list_y[i],list_z[i],shifts=dns)
        else:
            dist2_xy,dist2_z,dist2_r,weight = calc_dist_folded(list_x[i],list_y[i],list_z[i],unitcell,shifts=dns,)
        for k,dist2 in enumerate([dist2_xy,dist2_z,dist2_r]):
            average = np.mean(dist2,1)  # average over the atoms
            alldist2[:,i,k] = average
            #print i,list_x[i],it,average[:10]

            p = np.polyfit(lagtimes,average,1)
            allD[i,k] = p[0]   # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
        # if I want many figures:
        #fit_sqrt_vs_time(np.mean(dist_xy,1),dtc,outdir+"/fig_dist.xy.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_z,1), dtc,outdir+"/fig_dist.z.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_r,1), dtc,outdir+"/fig_dist.r.%i.png"%i,title=str(i))

    # extra figures
    m2_xy = np.mean(alldist2[:,:,0],1)
    s_xy = np.std(alldist2[:,:,0],1)
    m2_z  = np.mean(alldist2[:,:,1],1)
    s_z  = np.std(alldist2[:,:,1],1)
    m2_r  = np.mean(alldist2[:,:,2],1)
    s_r  = np.std(alldist2[:,:,1],1)
    verbose=False
    fit_sqrt_vs_time(np.sqrt(m2_xy),dtc*ddn,
            outdir+"/fig_dist.xy.average.png",title="average of %i"%nfiles,
            t0=lagtimes[0],std=np.sqrt(s_xy),verbose=verbose)
    fit_sqrt_vs_time(np.sqrt(m2_z), dtc*ddn,
            outdir+"/fig_dist.z.average.png",title="average of %i"%nfiles,
            t0=lagtimes[0],std=np.sqrt(s_z))
    fit_sqrt_vs_time(np.sqrt(m2_r), dtc*ddn,
            outdir+"/fig_dist.r.average.png",title="average of %i"%nfiles,
            t0=lagtimes[0],std=np.sqrt(s_r))

    store_msd(lagtimes,m2_xy,outdir+"/fig_dist.xy.average.txt",error=s_xy)
    store_msd(lagtimes,m2_z ,outdir+"/fig_dist.z.average.txt", error=s_z)
    store_msd(lagtimes,m2_r ,outdir+"/fig_dist.r.average.txt", error=s_r)

    print_output_D_ave(allD)


def analyze_matrixdist(list_x,list_y,list_z,dn1,outdir,dtc,dn2=None,ddn=1,unitcell=None,npt=False):
    "Take the average over the D estimates in each of these xyz trajectories"""
    assert len(list_x) > 0
    assert len(list_x) == len(list_y)
    assert len(list_x) == len(list_z)
    nfiles = len(list_x)
    """Conditional Mean Square Distance
    dn1  --  start shift
    dn2  --  end shift
    ddn  --  range(dn1,dn2,ddn)

    Example
      dn1=3, dn2=7, ddn=2
      then dns=[3,5,7], nlags=3, ntime should be 8 or more
    """
    if dn2 is None:
        dn2 = dn1
    assert dn2 >= dn1
    assert ddn >= 1
    lt1 = dn1*dtc
    lt2 = dn2*dtc  # I will fit in region lagtime1 to lagtime2
    dns = np.arange(dn1,dn2+1,ddn)
    lagtimes = dns*dtc
    nlags = len(lagtimes)

    ntime = list_x[0].shape[0]
    natom = list_x[0].shape[1]
    if dns[-1]>=ntime:
        raise ValueError("asking for too many shifts, max dn > ntime: %i,%i"%(dns[-1],ntime))

    #if nstep: lagtimes = np.arange(0,nstep*dtc,dtc)

    alldist2 = np.zeros((nlags,nfiles,6),float)
    allD = np.zeros((nfiles,6),float)

    print "="*5
    print "Results"
    print "making %i fits" %nfiles, "(number of trajectories)"
    print "fit from %i lagtimes, i.e. time %f ps to time %f ps, actually time %f ps" %(
             nlags,lagtimes[0],lagtimes[-1],(dn2-dn1)*dtc)
    print "calculating..."
    for i in range(nfiles):
        print "file",i
        # matrix A contains 6 components of correlation matrix
        if unitcell is None:
            A,weight = calc_dist(list_x[i],list_y[i],list_z[i],shifts=dns,matrix=True)
        else:
            A,weight = calc_dist_folded(list_x[i],list_y[i],list_z[i],unitcell,shifts=dns,matrix=True,npt=npt)
        for k,dist2 in enumerate(A):
            average = np.mean(dist2,1)  # average over the atoms
            alldist2[:,i,k] = average
            #print i,list_x[i],it,average[:10]

            p = np.polyfit(lagtimes,average,1)
            allD[i,k] = p[0]   # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
        # if I want many figures:
        #fit_sqrt_vs_time(np.mean(dist_xy,1),dtc,outdir+"/fig_dist.xy.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_z,1), dtc,outdir+"/fig_dist.z.%i.png"%i,title=str(i))
        #fit_sqrt_vs_time(np.mean(dist_r,1), dtc,outdir+"/fig_dist.r.%i.png"%i,title=str(i))

    # extra figures
    means = np.mean(alldist2,axis=1)   # nlags x 6
    stds  = np.std(alldist2,axis=1)     # nlags x 6
    mean_r = np.mean(alldist2[:,:,0]+alldist2[:,:,1]+alldist2[:,:,2],axis=1)
    std_r  = np.std(alldist2[:,:,0]+alldist2[:,:,1]+alldist2[:,:,2],axis=1)

    verbose=False
    labs = ["xx","yy","zz","xy","xz","yz"]
    for i in range(6):
        fit_sqrt_vs_time(means[:,i],dtc*ddn,
            outdir+"/fig_dist.%s.average.png"%(labs[i]),title="average of %i"%nfiles,
            t0=lagtimes[0],std=stds[:,i],verbose=verbose,sqrt=False)
    fit_sqrt_vs_time(mean_r,dtc*ddn,
            outdir+"/fig_dist.r.average.png",title="average of %i"%nfiles,
            t0=lagtimes[0],std=std_r,verbose=verbose,sqrt=False)
    # write files
    for i in range(6):
        store_msd(lagtimes,means[:,i],outdir+"/fig_dist.%s.average.txt"%(labs[i]),error=stds[:,i])
    store_msd(lagtimes,mean_r,outdir+"/fig_dist.%s.average.txt"%("r"),error=std_r)

    print_output_matrixD_ave(allD)


#=========================================


def analyze_dist_BIS1(list_x,list_y,list_z,dtc):
    "Collect distances in all these xyz trajectories"""
    assert len(list_x) > 0
    assert len(list_x) == len(list_y)
    assert len(list_x) == len(list_z)
    nfiles = len(list_x)

    print "="*5
    print "Results"
    #alllagtimes = []
    #alldist_xy = []
    #alldist_z = []
    #alldist_r = []
    allD = np.zeros((nfiles,3),float)

    for i in range(nfiles):
        lagtimes,dist2_xy,dist2_z,dist2_r = collect_dist(list_x[i],list_y[i],list_z[i],dtc)
        print "file",i,"shape",dist2_xy.shape
        for it,dist2 in enumerate([dist2_xy,dist2_z,dist2_r]):

            p = np.polyfit(lagtimes,dist2,1)
            allD[i,it] = p[0]   # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
            #alllagtimes.append(lagtimes)
            #alldist_xy.append(dist_xy)
            #alldist_z.append(dist_z)
            #alldist_r.append(dist_r)

    #lagtimes = np.array(alllagtimes).ravel()
    #dist_xy = np.array(alldist_xy).ravel()
    #dist_z = np.array(alldist_z).ravel()
    #dist_r = np.array(alldist_r).ravel()
    print_output_D_ave(allD)


#=========================================
# TIME-DEPENDENT D
#=========================================

def analyze_dist_timedependent(list_x,list_y,list_z,dtc,nstep,figname,zoom=50,shift=1):
    "Collect distances in all these xyz trajectories"""
    assert len(list_x) > 0
    assert len(list_x) == len(list_y)
    assert len(list_x) == len(list_z)
    nfiles = len(list_x)

    nstep = 1000
    print "="*5
    print "Results"

    allddr = np.zeros((nstep,nfiles,6),float)  # six of those    
    for i in range(nfiles):
        ddr,weight = calc_timedependent_D(list_x[i],list_y[i],list_z[i],dtc,shift=shift)
        for it,ddist in enumerate(ddr):
            allddr[:,i,it] = np.mean(ddr[it],axis=1)
            print "file",i,"type",it,"ddr",ddr[it].shape

    for it,label in enumerate(["xy1","xy2","z1","z2","r1","r2"]):
        dim = [2,2,1,1,3,3,][it]
        plot_vs_time(np.mean(allddr[:,:,it],axis=1) / (2.*dim) ,dtc,figname+".type-%s.shift"%label +str(shift)+".png")

def calc_timedependent_D_fromdir(dirname,dtc,figname,zoom=100,shift=1):
    x = np.array(read_coor(dirname+"/smoothcrd-x/out"))
    y = np.array(read_coor(dirname+"/smoothcrd-y/out"))
    z = np.array(read_coor(dirname+"/smoothcrd-z/out")) 
    ddr,weight = calc_timedependent_D(x,y,z,dtc,shift=shift)
    meanddr = np.mean(ddr,axis=1)  # average over atoms
    plot_vs_time(meanddr,dtc,figname+".png")
    plot_vs_time(meanddr[:zoom],dtc,figname+".zoom.png")
    return ddr,weight

def calc_timedependent_D_from3files(xfile,yfile,zfile,dtc,shift=1):
    x = np.array(read_coor(xfile))
    y = np.array(read_coor(yfile))
    z = np.array(read_coor(zfile))
    ddr,weight = calc_timedependent_D(x,y,z,dtc,shift=shift)
    return ddr,weight

def calc_timedependent_D(x,y,z,dtc,shift=1):
    """
    First approach:
        Calculate [dr**2(t+shift) - dr**2(t)] / shift as a function of shift,
        averaged over available times
    Second approach:
        Calculate [dr**2(t+shift) - dr**2(t)] / shift as a function of shift,
        averaged over available shifts"""
    nstep = x.shape[0]  # number of time steps
    natom = x.shape[1]  # number of atoms

    dist2_xy,dist2_z,dist2_r,weight = calc_dist(x,y,z)   # includes averaging

    ddr = []

    for it,dist2 in enumerate([dist2_xy,dist2_z,dist2_r]):
        # dist2 is Delta r**2(t), dimension nstep x natom
        #label = ["xy","z","r"][it]
        #plot_vs_time(dr2,dtc,"dr2.%s.png"%label)

        # first approach
        ddr1 = np.zeros((nstep,natom),float)
        ddr1[shift:,:] = (dist2[shift:,:]-dist2[:-shift,:]) / (shift*dtc)
        ddr1[0,:] = ddr1[1,:]  # do trick to fix first timestep

        # second approach
        ddr2 = np.zeros((nstep,natom),float)
        for sh in range(1,nstep):
            ddr2[sh,:] = np.mean(dist2[sh:,:]-dist2[:-sh,:],axis=0) / (sh*dtc)
        ddr2[0,:] = ddr2[1,:]  # do trick to fix first timestep

        # third approach
        #ddr3 = np.zeros((nstep,natom),float)
        #for shift in range(1,nstep):
        #    lt = np.arange(dtc,(nstep-shift+1)*dtc,dtc)
        #    ddr3[shift,:] = np.mean((dr2[shift:,:]-dr2[:-shift,:]).transpose() / (6.*lt),axis=1) 
        #ddr3[0,:] = ddr3[1,:]  # do trick to fix first timestep
        ddr.extend([ddr1,ddr2])

    return ddr,weight  # this is [ddxy1,ddxy2,ddz1,ddz2,ddr1,ddr2]


#=========================================
# USUAL POSITION-DEP FIT
#=========================================


def analyze_dist_condz_traditional(list_x,list_y,list_z,dn1,dtc,zpbc,figname,dn2=None,ddn=1,plain=True,nbins=50,surv=False):
    """Conditional Mean Square Distance
    dn1  --  start shift
    dn2  --  end shift
    ddn  --  range(dn1,dn2,ddn)
    surv  --  whether to use survival probability:
              False or True (divide MSD by P(t))
    """
    if surv: # True or divide # for survival probability
        from mcdiff.tools.functionsextract import indices_survived, calc_survival_probability
        from mcdiff.tools.functionsextract import calc_survival_probability_add

    if dn2 is None:
        dn2 = dn1
    assert dn2 >= dn1
    lt1 = dn1*dtc
    lt2 = dn2*dtc  # I will fit in region lagtime1 to lagtime2
    lagtimes = np.arange(dn1,dn2+1,ddn)*dtc
    nlags = len(lagtimes)

    nfiles = len(list_x)
    ntime = list_x[0].shape[0]
    natom = list_x[0].shape[1]

    # construct bins - I can play here with resolution
    edges = (np.arange(nbins+1)/float(nbins)-0.5)*zpbc
    mids = ((np.arange(nbins)+0.5)/float(nbins)-0.5)*zpbc
    print "edges condz",edges

    # fill up count and dz arrays
    count = np.zeros((nfiles,3,nbins,nlags),int)
    dz = np.zeros((nfiles,3,nbins,nlags),float)
    if surv:
        initials = np.zeros((nbins+2,nlags),float)
        surviveds = np.zeros((nbins+2,nlags),float)
    for n in range(nfiles):
        x = list_x[n]   # ntime x natom
        y = list_y[n]
        z = list_z[n]
        pbccrd_z = z[:,:]-zpbc*np.floor(z[:,:]/zpbc+0.5)

        for k,dn in enumerate(np.arange(dn1,dn2+1,ddn)):
            dist2_xy,dist2_z,dist2_r = calc_dist_lt(x,y,z,dn)  # (ntime-dn) x natom
            #print "file,dn",n,dn

            for at in range(natom):
                # initial z
                #zinit = z[:-dn,:]-zpbc*np.floor(z[:-dn,:]/zpbc+0.5)  # (ntime-dn) x natom
                zinit_digi = np.digitize(pbccrd_z[:-dn,at],edges)  # (ntime-dn)

                if surv:
                    indices = indices_survived(pbccrd_z[:,at],edges,shift=dn)
                else:
                    indices = range(len(zinit_digi))
                for i in indices:
                    digi = zinit_digi[i]
                    for j,dist2 in enumerate([dist2_xy,dist2_z,dist2_r]):
                        count[n,j,digi-1,k]+=1.   # do -1
                        dz[n,j,digi-1,k]+=dist2[i,at]
                if surv:
                    s1,s2,s3 = calc_survival_probability_add(initials[:,k],surviveds[:,k],pbccrd_z[:,at],edges,shift=dn)
            #if surv:
            #    survival,initial,survived = calc_survival_probability(z.transpose(),edges,shift=dn)

    # FIT  <r^2> = 2 dim D dn dtc

    if plain:  #use the last lagtime (endpoint)
        print "plain condz: use the last lagtime"
        DD = dz/count
        allD = DD[:,:,:,-1]/2./lagtimes[-1]
        allD[:,0,:] /= 2.   # dimension adapt
        allD[:,2,:] /= 3.
    
        mean = np.mean(allD,axis=0)
        std = np.std(allD,axis=0)

        # less sensitive to nans
        mean_dzcount = np.sum(dz,axis=0)/np.sum(count,axis=0)
        mean = mean_dzcount[:,:,-1]/2./lagtimes[-1]
        mean[0,:]/=2.
        mean[2,:]/=3.

    else:
        print "fit condz: using multiple lagtimes"
        DD = dz/count
        allD = np.zeros((nfiles,3,nbins),float)
        for j in range(3):
            for n in range(nfiles):
                for i in range(nbins):
                    p = np.polyfit(lagtimes,DD[n,j,i,:],1)
                    allD[n,j,i] = p[0]/2. # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
        allD[:,0,:] /= 2.   # dimension adapt
        allD[:,2,:] /= 3.

        mean = np.mean(allD,axis=0)
        std = np.std(allD,axis=0)

        # less sensitive to nans
        mean = np.zeros((3,nbins),float)
        mean_dzcount = np.sum(dz,axis=0)/np.sum(count,axis=0)
        for j in range(3):
            for i in range(nbins):
                p = np.polyfit(lagtimes,mean_dzcount[j,i,:],1)
                mean[j,i] = p[0]/2. # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s
        mean[0,:]/=2.
        mean[2,:]/=3.

    print "===== Results ====="
    print "lagtimes",lagtimes
    print "count",count.shape
    print "dz",dz.shape
    print "allD",allD.shape
    #print "====="
    #print "count",count
    #print "dz",dz
    #print "ratio",dz/count
    #print "allD",allD
    print "====="
    if surv:
        survivalprob = surviveds[1:-1,:]/initials[1:-1,:]
        print "surviveds",surviveds
        print "initials",initials
        print "survival probability",survivalprob
    if surv == "divide":
        print "===== MSD is divided by survival probability ====="
        mean[0,:] = mean[0,:]/survivalprob[:,-1]
        std[0,:]  = std[0,:]/survivalprob[:,-1]
    print "mean D",mean

    import matplotlib.pyplot as plt
    plt.figure()
    for j in range(3):
        for n in range(len(allD)): #range(nfiles):
            plt.plot(mids,allD[n,j,:],color='grey')
    plt.errorbar(mids,mean[0,:],yerr=std[0,:],color='red',lw='3',label='xy')
    plt.errorbar(mids,mean[1,:],yerr=std[1,:],color='green',lw='3',label='z')
    plt.errorbar(mids,mean[2,:],yerr=std[2,:],color='k',lw='3',label='r')
    plt.legend()
    plt.ylabel("D [A^2/ps]")
    #plt.ylim(0.1,1)
    
    plt.savefig(figname)

    # print to a file for later use
    f = file(figname+".txt","w+")
    print >> f, "#diffusion xy z r"
    print >> f, "#lagtimes",lagtimes
    print >> f, "#nfiles",nfiles
    print >> f, "#zpbc", zpbc
    #print >> f, "#edges", edges  #### TODO does not fit on one line
    print >> f, "#nbins", nbins
    for i in range(nbins):
        if surv:
            print >> f, mean[0,i],mean[1,i],mean[2,i],std[0,i],std[1,i],std[2,i],survivalprob[i]
        else:
            print >> f, mean[0,i],mean[1,i],mean[2,i],std[0,i],std[1,i],std[2,i]
    f.close()



def analyze_dist_condz_traditional_2(list_x,list_y,list_z,dn,dtc,zpbc,figname,nbins=50):
    lt = dn*dtc

    nfiles = len(list_x)
    ntime = list_x[0].shape[0]
    natom = list_x[0].shape[1]

    # construct bins - I can play here with resolution
    bins = np.arange(-zpbc/2.,zpbc/2.+0.0001,zpbc/nbins)
    print "bins",bins
    dz = [[[[] for i in range(nbins)] for i in range(3)] for i in range(nfiles)]
    # fill up count and dz arrays
    for n in range(nfiles):
        x = list_x[n]   # ntime x natom
        y = list_y[n]
        z = list_z[n]
        dist_x = calc_onedist_lt(x,dn)  # (ntime-dn) x natom
        dist_y = calc_onedist_lt(y,dn)  # (ntime-dn) x natom
        dist_z = calc_onedist_lt(z,dn)  # (ntime-dn) x natom
 
        # (ntime-dn) x natom    initial z
        zinit = z[:-dn,:]-zpbc*np.floor(z[:-dn,:]/zpbc+0.5)

        for at in range(natom):
            zinit_digi = np.digitize(zinit[:,at],bins)  # (ntime-dn) x natom
            for i,digi in enumerate(zinit_digi):
                for j,dist in enumerate([dist_x,dist_y,dist_z]):
                    dz[n][j][digi-1].append(dist[i,at])

    # FIT  <r^2> = 2 dim D lt
    allD = np.zeros((nfiles,3,nbins),float)
    for j in range(3):
        for n in range(nfiles):
            for i in range(nbins):
                a = dz[n][j][i]
                m = np.mean(a)
                s = np.std(a)
                b2 = (a-m)**2
                M = np.mean(b2)
                allD[n,j,i] = M/2./lt # a_1 this is in angstrom**2/ps = 1e-20/1e-12 meter**2/second
                                # = 1e-8 meter**2/second = 1e-4 cm**2/s

    print "===== Results ====="
    print "allD",allD.shape
    print allD
 
    mean = np.mean(allD,axis=0)
    std = np.std(allD,axis=0)
    print "mean D"
    print mean
    print "std D"
    print std

    x = bins[:-1] + zpbc/(2.*nbins)
    import matplotlib.pyplot as plt
    plt.figure()
    for j in range(3):
        for n in range(nfiles):
            plt.plot(x,allD[n,j,:],color='grey')
    plt.errorbar(x,mean[0,:],yerr=std[0,:],color='red',lw='3',label="x")
    plt.errorbar(x,mean[1,:],yerr=std[1,:],color='green',lw='3',label="y")
    plt.errorbar(x,mean[2,:],yerr=std[2,:],color='k',lw='3',label="z")
    plt.ylabel("D [A^2/ps]")
    #plt.ylim(0.1,1)
    plt.legend()
    plt.savefig(figname)

    # print to a file for later use
    f = file(figname+".txt","w+")
    print >> f, "#diffusion xy z r"
    print >> f, "#nfiles",nfiles
    print >> f, "#zpbc", zpbc
    for i in range(nbins):
        print >> f, mean[0,i],mean[1,i],mean[2,i],std[0,i],std[1,i],std[2,i]
    f.close()


#=========================================
# CONDITIONAL Z
#=========================================

def analyze_dist_condz(list_x,list_y,list_z,dtc,zpbc,dn,figname,nbins,tradition=False):
    "Collect distances in all these three trajectories"""
    assert len(list_x) > 0
    assert len(list_x) == len(list_y)
    assert len(list_x) == len(list_z)
    nfiles = len(list_x)

    print "="*5
    print "Results"

    alldist2_xy = []
    alldist2_z = []
    alldist2_r = []
    allz_init = []
    allz_final = []
    for i in range(nfiles):
        dist2_xy,dist2_z,dist2_r = calc_dist_lt(list_x[i],list_y[i],list_z[i],dn)
        z = np.array(list_z[i])
        #print "z.shape",z.shape
        ntime = z.shape[0]
        natom = z.shape[1]

        alldist2_xy.append(dist2_xy)
        alldist2_z.append(dist2_z)
        alldist2_r.append(dist2_r)

        # initial z
        zinit = z[:-dn,:]-zpbc*np.floor(z[:-dn,:]/zpbc+0.5)
        allz_init.append(zinit)

        # final z
        zfinal = z[dn:,:]-zpbc*np.floor(z[dn:,:]/zpbc+0.5)
        allz_final.append(zfinal)

    zbins = np.arange(nbins+1)*zpbc/float(nbins) -zpbc/2.
    print "zbins",zbins
    rbins = np.arange(0,50.1,0.5)  ################ hard coded TODO

    #if not tradition:
    #    analyze_dist_condz_essence(alldist2_xy,
    #        alldist2_z,alldist2_r,allz_init,allz_final,dn,dtc,figname,zbins,rbins)
    #else:  # NOOOOO not tested TODO
    #    print "Not tested yet."
    #    pass
#def analyze_dist_condz_essence(alldist2_xy,alldist2_z,alldist2_r,allz_init,allz_final,dn,dtc,figname,zbins,rbins):
#    nfiles = len(alldist2_xy)
#    zpbc = zbins[-1]-zbins[0]

    lt = dn*dtc
    print "dn*dtc",lt
    if lt < 0.6:
        distmax = 2.
    elif lt < 6.:  #ps
        distmax = 4.
    elif lt < 60.:
        distmax = 9.
    else:
        distmax = 15.
    #distmax = None

    for c,allz in enumerate([allz_init]): #,allz_final]):
      mean = np.zeros((3,len(zbins)-1),float)
      std = np.zeros((3,len(zbins)-1),float)
      print "="*10
      labelz = ["zinit","zfinal"][c]
      print "labelz",labelz

      for i,dist2 in enumerate([alldist2_xy,alldist2_z,alldist2_r]):
        label = labelz+"-"+["xy","z","r"][i]
        #factor = [np.sqrt(2),1.,np.sqrt(3)][i]  # rescaling

        # 2D bins x=axis0, y=axis1
        #k, xedges,yedges = np.histogram2d(np.sqrt(np.array(dist2)).ravel(),np.array(allz).ravel(),[rbins,zbins],normed=True)
        k2, xedges,yedges = np.histogram2d(np.array(dist2).ravel(),np.array(allz).ravel(),[rbins,zbins],normed=True)
        #if i in [0,2]:
        #    k2,xedges,yedges = np.histogram2d(np.array(dist2).ravel(),np.array(allz).ravel(),[len(zbins),len(zbins)],normed=True)
        #else:
            #bins = zbins[len(zbins)/2:]
        #    k2,xedges,yedges = np.histogram2d(np.array(dist2).ravel(),np.array(allz).ravel(),[len(zbins),len(zbins)],normed=True)
        #print dist2_r.shape,z.shape
        print "hist,xedges,yedges",k2.shape, xedges.shape, yedges.shape
        for n,donorm in enumerate([False,True]):
            Label = label+"-%s" %(["nonorm","norm"][n])
            print "Label",Label
            import copy
            kk = copy.deepcopy(k2)
            if donorm:  # normalized
                norm = np.sum(kk,axis=0)
                kk = kk / norm

            # expectation value
            d2 = ((xedges[1:]+xedges[:-1]).reshape((-1,1))/2.)   # these are rbins**2 in middle
            xmiddle = (xedges[1:]+xedges[:-1])/2.    # these are rbins**2 in middle
            ymiddle = (yedges[1:]+yedges[:-1])/2.    # these are zbins in middle
            print "d2",d2.shape, "k2",k2.shape, "mean",mean.shape, "x",xmiddle.shape
            mean[i,:] = np.sum(d2*k2,axis=0)/np.sum(k2,axis=0)    # <r^2> is independent of "norm/nornorm"  ######
            std[i,:] = np.sum((d2-mean[i,:])**2*k2,axis=0)/np.sum(k2,axis=0)

            import matplotlib.pyplot as plt
            plt.figure()
            plt.contourf(np.sqrt(xmiddle),ymiddle,kk.transpose()) #locator=ticker.LogLocator()

            plt.plot(np.sqrt(mean[i,:]),ymiddle,color="k")
            #D = E**2 / 2. /factor**2/dn*10 ########################################################3
            #plt.plot(D,yedges[:-1],color="grey",lw=2)

            plt.xlabel("distance [A]")
            plt.xlim(xmax=distmax)
            plt.ylabel("z [A]")
            plt.title("MSD: "+Label)
            plt.colorbar()
            plt.savefig(figname+"_hist2d.%s.dn%i.png"%(Label,dn))

      # print to a file for later use
      f = file(figname+"_hist2d.%s.dn%i.txt"%(labelz,dn),"w+")
      print >> f, "#diffusion xy z r"
      print >> f, "#nfiles",nfiles
      print >> f, "#zpbc", zpbc
      print >> f, "#dn", dn
      for i in range(len(zbins)-1):
        # mean = <r**2> = 6*D*lt, so D = <r**2>/2/dim/lt
        print >> f, mean[0,i]/4./lt,mean[1,i]/2./lt,mean[2,i]/6./lt,std[0,i],std[1,i],std[2,i]
      f.close()

#=========================================
# PRINT AVERAGE D
#=========================================


def print_output_D_ave(allD):
    print "="*20
    print "Diffusion estimates"
    print allD.shape
    #print "xy,  z,  r"
    #print allD

    print "="*5
    print "xy"
    print allD[:,0]/4.  # 2D
    print "z"
    print allD[:,1]/2.  # 1D
    print "r"
    print allD[:,2]/6.  # 3D

    print "="*5
    print "Diffusion constant"
    print "   %20s   %20s" %("Dmean[e-4cm^2/s]","Dstd")
    print "xy %20.10f   %20.10f" %(np.mean(allD[:,0])/4., np.std(allD[:,0])/4.)
    print "z  %20.10f   %20.10f" %(np.mean(allD[:,1])/2., np.std(allD[:,1])/2.)
    print "r  %20.10f   %20.10f" %(np.mean(allD[:,2])/6., np.std(allD[:,2])/6.)
    print "="*5

def print_output_matrixD_ave(allD):
    print "="*20
    print "Diffusion estimates"
    print allD.shape

    print "="*5
    labs = ["xx","yy","zz","xy","xz","yz"]
    for i in range(6):
        print labs[i]
        print allD[:,i]/2.  # 2D
    print "="*5
    print "yzplane"
    print (allD[:,0]+allD[:,1])/4.  # 2D
    print "r-3D"
    print (allD[:,0]+allD[:,1]+allD[:,2])/6.  # 3D

    print "="*5
    print "Diffusion constant"
    print "   %20s   %20s" %("Dmean[e-4cm^2/s]","Dstd")
    print "xx %20.10f   %20.10f" %(np.mean(allD[:,0])/2., np.std(allD[:,0])/2.)
    print "yy %20.10f   %20.10f" %(np.mean(allD[:,1])/2., np.std(allD[:,1])/2.)
    print "zz %20.10f   %20.10f" %(np.mean(allD[:,2])/2., np.std(allD[:,2])/2.)
    print "xy %20.10f   %20.10f" %(np.mean(allD[:,3])/2., np.std(allD[:,3])/2.)
    print "xz %20.10f   %20.10f" %(np.mean(allD[:,4])/2., np.std(allD[:,4])/2.)
    print "yz %20.10f   %20.10f" %(np.mean(allD[:,5])/2., np.std(allD[:,5])/2.)
    print "="*5
    print "XY %20.10f   %20.10f" %(np.mean(allD[:,0]+allD[:,1])/4., np.std(allD[:,0]+allD[:,1])/4.)
    print "Z  %20.10f   %20.10f" %(np.mean(allD[:,2])/2., np.std(allD[:,2])/2.)
    print "R  %20.10f   %20.10f" %(np.mean(allD[:,0]+allD[:,1]+allD[:,2])/6., np.std(allD[:,0]+allD[:,1]+allD[:,2])/6.)
    print "="*5
    analyze_as_tensor(allD)

# to convert
    #B = np.empty([3,3])   # I should do a hard copy?
    #for i in range(3):
    #    B[i,i] = A[:,i]
    #B[0,1]=A[:,3]; B[0,2]=A[:,4]; B[1,2]=A[:,5]
    #B[1,0]=A[:,3]; B[2,0]=A[:,4]; B[2,1]=A[:,5]
    #D = np.array([A[0],A[3],A[4],A[3],A[1],A[5],A[4],A[5],A[2]])

def tensor_list_to_matrix_2D(A):
    B = np.array([A[:,0],A[:,3],A[:,4],A[:,3],A[:,1],A[:,5],A[:,4],A[:,5],A[:,2]])
    C = np.reshape(B,(3,-1,len(A)))
    print "list",A.shape
    print "matrix",C.shape
    #aveC = np.mean(C,axis=-1)
    #print "matrix-average",aveC.shape
    #print aveC
    return C

def tensor_list_to_matrix_1D(A):
    B = np.zeros((3,3))    # I should do a hard copy?
    for i in range(3):
        B[i,i] = A[i]
    B[0,1]=A[3]; B[0,2]=A[4]; B[1,2]=A[5]
    B[1,0]=A[3]; B[2,0]=A[4]; B[2,1]=A[5]
    print "list",A.shape
    print "matrix",B.shape
    return B

def analyze_as_tensor(allD):
    print "="*5
    print "Diffusion tensor - eigenvalues"
    H = tensor_list_to_matrix_2D(allD/2.)
    nruns = H.shape[-1]
    print "="*5
    print "1. average over eigenvalues"
    vals0 = []
    for i in range(nruns):
        vals,vecs = np.linalg.eigh(H[:,:,i])
        vals0.append(vals)
    vals0 = np.array(vals0)
    mean = np.mean(vals0,axis=0)
    std = np.std(vals0,axis=0)
    print "mean vals"
    for i in range(3): print mean[i]
    print "std vals"
    for i in range(3): print std[i]

    print "="*5
    print "2. average matrices, then take eigenvalues"
    means = np.mean(allD,axis=0)
    A = tensor_list_to_matrix_1D(means/2.)
    vals,vecs = np.linalg.eigh(A)
    print "vals mean"
    for i in range(3): print vals[i]
    print "vecs mean"
    for i in range(3):
        print vecs[i,0],vecs[i,1],vecs[i,2]

def print_output_D_ave_1D(allD):
    print "="*20
    print "Diffusion estimates"
    print allD.shape
    #print allD

    print "="*5
    print allD[:]/2.  # 1D

    print "="*5
    print "Diffusion constant"
    print "   %20s   %20s" %("Dmean[e-4cm^2/s]","Dstd")
    print "r  %20.10f   %20.10f" %(np.mean(allD[:])/2., np.std(allD[:])/2.)
    print "="*5

#=========================================

def calc_dist_fromdir(dirname):
    x = np.array(read_coor(dirname+"/smoothcrd-x/out"))
    y = np.array(read_coor(dirname+"/smoothcrd-y/out"))
    z = np.array(read_coor(dirname+"/smoothcrd-z/out"))
    dist2_xy,dist2_z,dist2_r,weight = calc_dist(x,y,z)
    return dist2_xy,dist2_z,dist2_r,weight

def calc_dist_from3files(xfile,yfile,zfile,rv=False):
    x = np.array(read_coor(xfile,rv=rv,axis=0))
    y = np.array(read_coor(yfile,rv=rv,axis=1))
    z = np.array(read_coor(zfile,rv=rv,axis=2))
    dist2_xy,dist2_z,dist2_r,weight = calc_dist(x,y,z)
    return dist2_xy,dist2_z,dist2_r,weight

def calc_dist_lt_from3files(xfile,yfile,zfile,dn,rv=False):
    x = np.array(read_coor(xfile,rv=rv,axis=0))
    y = np.array(read_coor(yfile,rv=rv,axis=1))
    z = np.array(read_coor(zfile,rv=rv,axis=2))
    d2_xy,d2_z,d2_r = calc_dist_lt(x,y,z,dn)
    return d2_xy,d2_z,d2_r

def collect_dist_from3files(xfile,yfile,zfile,dtc):
    x = np.array(read_coor(xfile))
    y = np.array(read_coor(yfile))
    z = np.array(read_coor(zfile))
    lagtimes,dist2_xy,dist2_z,dist2_r = collect_dist(x,y,z,dtc)
    return lagtimes,dist2_xy,dist2_z,dist2_r

#=========================================

def calc_dist_lt(x,y,z,dn):
    dist2_xy = (x[:-dn,:] - x[dn:,:])**2 + (y[:-dn,:] - y[dn:,:])**2
    dist2_z  = (z[:-dn,:] - z[dn:,:])**2
    dist2_r = dist2_xy + dist2_z
    return dist2_xy,dist2_z,dist2_r

def calc_matrixdist_lt(x,y,z,dn):
    dx = x[dn:,:]-x[:-dn,:]
    dy = y[dn:,:]-y[:-dn,:]
    dz = z[dn:,:]-z[:-dn,:]
    A = [dx**2,dy**2,dz**2,dx*dy,dx*dz,dy*dz]
    return A

def calc_onedist_lt(x,dn):
    dist  = x[dn:,:] - x[:-dn,:]  # end-start
    return dist

def calc_dist_1D(x,shifts=None):
    # kind of oversampling!
    # Use ALL data in the files !!!
    # coor format: x[timestemp,atom]
    # returns: dist2: nstep x natom
    # I already average over the shifted time origin
    if shifts is None:
        nstep = x.shape[0]  # number of time steps
        shifts = np.arange(nstep)
    nlags = len(shifts)
    natom = x.shape[1]  # number of atoms
    dist2  = np.zeros((nlags,natom),float)
    # fill up
    for i,dn in enumerate(shifts):  # dn is shift (lagtime)
        if dn > 0:
            diff  = (x[:-dn,:] - x[dn:,:])**2
            dist2[i,:]  = np.mean(diff,axis=0)   #z/(self.nstep-dn)
    return dist2

def calc_dist(x,y,z,shifts=None,matrix=False):
    # kind of oversampling!
    # Use ALL data in the files !!!
    # coor format: x[timestemp,atom]
    # I already average over the shifted time origin
    if shifts is None:
        nstep = x.shape[0]  # number of time steps
        shifts = np.arange(nstep)
    nlags = len(shifts)
    natom = x.shape[1]  # number of atoms
    weight  = np.zeros((nlags),float)
    if not matrix:
        dist2_xy = np.zeros((nlags,natom,),float)
        dist2_z  = np.zeros((nlags,natom,),float) 
        # fill up
        for i,dn in enumerate(shifts):  # dn is shift (lagtime)
            if dn > 0:
                diff2_xy = (x[:-dn,:] - x[dn:,:])**2 + (y[:-dn,:] - y[dn:,:])**2
                diff2_z  = (z[:-dn,:] - z[dn:,:])**2
                dist2_xy[i,:] = np.mean(diff2_xy,axis=0)  # xy2/(self.nstep-lt)
                dist2_z[i,:]  = np.mean(diff2_z,axis=0)   #z/(self.nstep-lt)
                weight[i] = len(diff2_xy)

        dist2_r = dist2_xy+dist2_z
        return dist2_xy,dist2_z,dist2_r,weight

    else:
        alldist = [np.zeros((nlags,natom),float) for i in range(6)]
        # fill up
        for i,dn in enumerate(shifts):  # dn is shift (lagtime)
            if dn > 0:
                A = calc_matrixdist_lt(x,y,z,dn)
                for j in range(6):
                    alldist[j][i,:] = np.mean(A[j],axis=0)
                weight[i] = len(A[0])
        return alldist,weight

def collect_dist(x,y,z,dtc):
    # without averaging over the shifted time origin
    # returns: XXXX
    lagtimes = []
    dist2_xy = []
    dist2_z = []
    dist2_r = []
    natom = x.shape[1]
    for dn in range(1,len(x)):  # dn is shift, dn*dtc is lagtime
        diff_xy = (x[:-dn,:] - x[dn:,:])**2 + (y[:-dn,:] - y[dn:,:])**2
        diff_z  = (z[:-dn,:] - z[dn:,:])**2
        lagtimes.extend(dn*np.ones(len(diff_xy)*natom)*dtc)
        dist2_xy.extend(diff_xy.ravel().tolist())
        dist2_z.extend(diff_z.ravel().tolist())
    lagtimes = np.array(lagtimes)
    dist2_xy = np.array(dist2_xy)
    dist2_z = np.array(dist2_z)
    dist2_r = dist2_xy+dist2_z
    return lagtimes,dist2_xy,dist2_z,dist2_r

def calc_dist_folded(x,y,z,unitcells,shifts=None,matrix=False,npt=False):
    """New: take into account pbc
    danger of accumulative error

    x -- x-coordinates of positions, ntime x natom
    y -- y-coordinates of positions, ntime x natom
    z -- z-coordinates of positions, ntime x natom
    unitcells -- array with unit cells of each time step, should
                 be the same for every time step, ntime x 3 x 3,
                 columns are the cell vectors
    with
    ntime -- number of time steps
    natom -- number of atoms
    """
    # kind of oversampling!
    # Use ALL data in the files !!!
    # coor format: x[timestep,atom]
    # I already average over the shifted time origin
    ntime = x.shape[0]  # number of time steps
    natom = x.shape[1]  # number of atoms
    if shifts is None:
        shifts = np.arange(ntime)
    assert ntime>1    # not useful if not enough frames
    assert shifts[-1]<ntime
    nlags = len(shifts)
    if not matrix:
        dist2_xy = np.zeros((nlags,natom,),float)
        dist2_z  = np.zeros((nlags,natom,),float)
    else:
        alldist = [np.zeros((nlags,natom),float) for i in range(6)]
    weight  = np.zeros((nlags),float)

    # construct differences dpos, all of them
    pos = np.array([x,y,z]).transpose()   # natom x ntime x 3
    dpos = pos[:,1:,:]-pos[:,:-1,:]  # natom x (ntime-1) x 3
    if len(dpos.shape) < 3:
        # in case I have just one atom, ore only 2 time steps
        print "WARNING, RESHAPING dpos IN FUNCTION calc_dist_folded"
        dpos = np.reshape(dpos,(natom,ntime-1,3))

    # pbc manipulations
    if not npt:
        for i in range(len(unitcells)):  # consistency check
            assert unitcells[i,0,0] == unitcells[0,0,0]
        reciproc = np.linalg.inv(unitcells[0,:,:]).transpose()  # (unitcell^T)^(-1)

        # direct coordinates
        dpos_direct = np.dot(dpos,reciproc)   # direct coordinates = cartesian . reciproc
        dpos_direct -= np.round(dpos_direct)
        # overwrite differences dpos (cartesian)
        dpos = np.dot(dpos_direct,unitcells[0,:,:].transpose())  # cartesian = direct coordinates . unitcell^T
    else:  # unitcell not constant in time
        reciproc = np.zeros(unitcells.shape,float)
        for i in range(len(unitcells)):
            reciproc[i,:,:] = np.linalg.inv(unitcells[i,:,:]).transpose()  # (unitcell^T)^(-1)
        reciproc = reciproc[:-1,:,:]

        # direct coordinates
        dpos_direct = np.einsum('ijk,jkm->ijm',dpos,reciproc)
        #dpos_direct = np.zeros(dpos.shape,float)
        #for i in range(len(unitcells)-1):
        #    dpos_direct[:,i,:] = np.dot(dpos[:,i,:],reciproc[i,:,:])   # direct coordinates = cartesian . reciproc
        dpos_direct -= np.round(dpos_direct)
        # overwrite differences dpos (cartesian)
        dpos = np.einsum('ijk,jkm->ijm',dpos_direct,unitcells[:-1,:,:])
        #for i in range(len(unitcells)-1):
        #    dpos[:,i,:] = np.dot(dpos_direct[:,i,:],unitcells[i,:,:].transpose())  # cartesian = direct coordinates . unitcell^T


    # save distribution of differences
    if False:
        dpos_direct = np.dot(dpos,reciproc)   # direct coordinates
        # put back or not: dpos = pos[:,1:,:]-pos[:,:-1,:]  # natom x (ntime-1) x 3
        f = file("differences_cart.dat","w+")
        g = file("differences_direct.dat","w+")
        for i in xrange(len(dpos)):
          for j in xrange(dpos.shape[1]):
            print >> f, dpos[i,j,0],dpos[i,j,1],dpos[i,j,2],dpos[i,j,0],dpos[i,j,1],dpos[i,j,2]
            print >> g, dpos_direct[i,j,0],dpos_direct[i,j,1],dpos_direct[i,j,2],dpos_direct[i,j,0],dpos_direct[i,j,1],dpos_direct[i,j,2]
        f.close()
        g.close()

    for i,dn in enumerate(shifts):  # dn is shift (lagtime)
        assert dn >= 0
        assert dn < ntime # should be the case already
        if dn > 0:
            ndiff = ntime-dn
            diff2 = np.zeros((natom,ndiff,3))
            #print "pos,dpos,dn,ndiff,diff2",pos.shape,dpos.shape,dn,ndiff,diff2.shape
            # time origin shifting
            for st in range(ndiff):
                end = st+dn
                diff2[:,st,:] = np.sum(dpos[:,st:end,:],axis=1)

            # average over time origin shifting 
            if not matrix:
                dist2_xy[i,:] = np.mean(diff2[:,:,0]**2+diff2[:,:,1]**2,axis=1)
                dist2_z[i,:] = np.mean(diff2[:,:,2]**2,axis=1)
            else:
                for k in range(3):
                    alldist[k][i,:] = np.mean(diff2[:,:,k]**2,axis=1)
                alldist[3][i,:] = np.mean(diff2[:,:,0]*diff2[:,:,1],axis=1)
                alldist[4][i,:] = np.mean(diff2[:,:,0]*diff2[:,:,2],axis=1)
                alldist[5][i,:] = np.mean(diff2[:,:,1]*diff2[:,:,2],axis=1)
            weight[i] = ndiff

    if not matrix:
        dist2_r = dist2_xy+dist2_z
        return dist2_xy,dist2_z,dist2_r,weight
    else:
        return alldist,weight


#### PLOT ####
def plot_vs_time(x,dt,filename,**kwargs):
    plt.figure()
    t = np.arange(len(x))*dt
    plt.plot(t,x,**kwargs)
    plt.xlabel("t [ps]")
    plt.savefig(filename)




