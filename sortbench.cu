#include <cuda.h>
#include <stdio.h>

__global__
void prefix_scan_8_0_shmem(unsigned char *keys, int nitems, int *pfxs) {
    __shared__ int sh_pfxs[256];

    if (threadIdx.y < 8)
        sh_pfxs[threadIdx.y * 32 + threadIdx.x] = 0;

    __syncthreads();

    int blksz = blockDim.x * blockDim.y;
    int cap = nitems * (blockIdx.x + 1);

    for (int i = threadIdx.y * 32 + threadIdx.x + nitems * blockIdx.x;
         i < cap; i += blksz) {
        int value = keys[i];
        atomicAdd(sh_pfxs + value, 1);
    }

    __syncthreads();

    if (threadIdx.y < 8) {
        int off = threadIdx.y * 32 + threadIdx.x;
        atomicAdd(pfxs + off, sh_pfxs[off]);
    }
}

#define GRP_RDX_FACTOR (GRPSZ / RDXSZ)
#define GRP_BLK_FACTOR (GRPSZ / BLKSZ)
#define GRPSZ 8192
#define RDXSZ 256
#define BLKSZ 512

__global__
void prefix_scan(unsigned short *keys, int *pfxs, const int shift) {
    const int tid = threadIdx.y * 32 + threadIdx.x;
    __shared__ int shr_pfxs[BLKSZ];

    shr_pfxs[tid] = 0;
    __syncthreads();
    int i = tid + GRPSZ * blockIdx.x;

    for (int j = 0; j < GRP_BLK_FACTOR; j++) {
        int value = (keys[i] >> shift) && 0xff;
        atomicAdd(shr_pfxs + value, 1);
        i += BLKSZ;
    }

    __syncthreads();
    pfxs[tid + BLKSZ * blockIdx.x] = shr_pfxs[tid];
}

__global__
void prefix_scan_8_0_shmem_shortseg(unsigned char *keys, int *pfxs) {
    const int tid = threadIdx.y * 32 + threadIdx.x;
    __shared__ int shr_pfxs[RDXSZ];

    if (tid < RDXSZ) shr_pfxs[tid] = 0;
    __syncthreads();

    // TODO: this introduces a hard upper limit of 512M keys (3GB) sorted in a
    // pass. It'll be a while before we get the 8GB cards needed to do this.
    int i = tid + GRPSZ * blockIdx.x;

    for (int j = 0; j < GRP_BLK_FACTOR; j++) {
        int value = keys[i];
        atomicAdd(shr_pfxs + value, 1);
        i += BLKSZ;
    }

    __syncthreads();
    if (tid < RDXSZ) pfxs[tid + RDXSZ * blockIdx.x] = shr_pfxs[tid];
}

__global__
void crappy_split(int *pfxs, int *pfxs_out) {
    const int blksz = 256;
    const int tid = threadIdx.y * 32 + threadIdx.x;
    int i = blksz * (tid + blockIdx.x * blksz);
    int i_bound = i + blksz;
    int val = 0;
    for (; i < i_bound; i++) {
        pfxs_out[i] = val;
        val += pfxs[i];
    }
}

__global__
void better_split(int *pfxs_out, const int *pfxs) {
    // This one must be launched as 32x1, regardless of BLKSZ.
    const int tid = threadIdx.x;
    const int tid5 = tid << 5;
    __shared__ int swap[1024];

    int base = RDXSZ * 32 * blockIdx.x;

    int value = 0;

    // Performs a fast "split" (don't know why I called it that, will rename
    // soon). For each entry in pfxs (corresponding to the number of elements
    // per radix in a group), this writes the exclusive prefix sum for that
    // group. This is in fact a bunch of serial prefix sums in parallel, and
    // not a parallel prefix sum.
    //
    // The contents of 32 group radix counts are loaded in 32-element chunks
    // into shared memory, rotated by 1 unit each group to avoid bank
    // conflicts. Each thread in the warp sums across each group serially,
    // updating the values as it goes, then the results are written coherently
    // to global memory.
    //
    // This leaves the processor extremely compute-starved, as this only allows
    // 12 warps per SM. It might be better to halve the chunk size and lose
    // some coalescing efficiency; need to benchmark. It's a relatively cheap
    // step overall though.

    for (int j = 0; j < 8; j++) {
        int jj = j << 5;
        for (int i = 0; i < 32; i++) {
            int base_offset = (i << 8) + jj + base + tid;
            int swap_offset = (i << 5) + ((i + tid) & 0x1f);
            swap[swap_offset] = pfxs[base_offset];
        }

#pragma unroll
        for (int i = 0; i < 32; i++) {
            int swap_offset = tid5 + ((i + tid) & 0x1f);
            int tmp = swap[swap_offset];
            swap[swap_offset] = value;
            value += tmp;
        }

        for (int i = 0; i < 32; i++) {
            int base_offset = (i << 8) + jj + base + tid;
            int swap_offset = (i << 5) + ((i + tid) & 0x1f);
            pfxs_out[base_offset] = swap[swap_offset];
        }
    }
}

__global__
void prefix_sum(int *pfxs, int nitems, int *out_pfxs, int *out_sums) {
    // Needs optimizing (later). Should be rolled into split.
    // Must launch 32x8.
    const int tid = threadIdx.y * 32 + threadIdx.x;
    const int blksz = 256;
    int val = 0;
    for (int i = tid; i < nitems; i += blksz) val += pfxs[i];

    out_pfxs[tid] = val;

    // I know there's a better way to implement this summing network,
    // but it's not a time-critical piece of code.
    __shared__ int sh_pfxs[blksz];
    sh_pfxs[tid] = val;
    val = 0;
    __syncthreads();
    // Intentionally exclusive indexing here, val{0} should be 0
    for (int i = 0; i < tid; i++) val += sh_pfxs[i];
    out_sums[tid] = val;

    // Here we shift things over by 1, to make retrieving the
    // indices and differences easier in the sorting step.
    int i;
    for (i = tid; i < nitems; i += blksz) {
        int t = pfxs[i];
        pfxs[i] = val;
        val += t;
    }
    // Now write the last column and we're done.
    pfxs[i] = val;
}

__global__
void sort_8(unsigned char *keys, int *sorted_keys, int *pfxs) {
    const int tid = threadIdx.y * 32 + threadIdx.x;
    const int blk_offset = GRPSZ * blockIdx.x;
    __shared__ int shr_pfxs[RDXSZ];

    if (tid < RDXSZ) shr_pfxs[tid] = pfxs[RDXSZ * blockIdx.x + tid];
    __syncthreads();

    int i = tid;
    for (int j = 0; j < GRP_BLK_FACTOR; j++) {
        int value = keys[i+blk_offset];
        int offset = atomicAdd(shr_pfxs + value, 1);
        sorted_keys[offset] = value;
        i += BLKSZ;
    }
}

#undef BLKSZ
#define BLKSZ 1024
__global__
void sort_8_a(unsigned char *keys, int *sorted_keys,
              const int *pfxs, const int *split) {
    const int tid = threadIdx.y * 32 + threadIdx.x;
    const int blk_offset = GRPSZ * blockIdx.x;
    __shared__ int shr_offs[RDXSZ];
    __shared__ int defer[GRPSZ];

    const int pfx_i = RDXSZ * blockIdx.x + tid;
    if (tid < RDXSZ) shr_offs[tid] = split[pfx_i];
    __syncthreads();

    for (int i = tid; i < GRPSZ; i += BLKSZ) {
        int value = keys[i+blk_offset];
        int offset = atomicAdd(shr_offs + value, 1);
        defer[offset] = value;
    }
    __syncthreads();

    // This calculation is a bit odd.
    //
    // For a given radix value 'r', shr_offs[r] currently holds the first index
    // of the *next* radix in defer[] (i.e.  if there are 28 '0'-radix values
    // in defer[], shr_offs[0]==28). We want to get back to a normal exclusive
    // prefix, so we subtract shr_offs[0] from everything.
    //
    // In the next block, we want to be able to find the correct position for a
    // value in defer[], given that value's index 'i' and its radix 'r'. This
    // requires two values: the destination index in sorted_keys[] of the first
    // value in the group with radix 'r' (given by pfxs[BASE + r]), and the
    // number of radix-'r' values before this one in defer[]. So, ultimately,
    // we want an equation in the inner loop below that looks like this:
    //
    //      int dst_offset = pfxs[r] + i - (shr_offs[r] - shr_offs[0]);
    //      sorted_keys[dst_offset] = defer[i];
    //
    // Of course, this generates tons of memory lookups and bank conflicts so
    // we precombine some of this here.
    int off0 = shr_offs[0];
    if (tid < RDXSZ) shr_offs[tid] = pfxs[0] - (shr_offs[tid] - off0);
    __syncthreads();

    int i = tid;
#pragma unroll
    for (int j = 0; j < GRP_BLK_FACTOR; j++) {
        int value = defer[i];
        int offset = shr_offs[value] + i;
        sorted_keys[offset] = value;
        i += BLKSZ;
    }
}



__global__
void prefix_scan_8_0_shmem_lessconf(unsigned char *keys, int nitems, int *pfxs) {
    __shared__ int sh_pfxs_banked[256][32];

    for (int i = threadIdx.y; i < 256; i += blockDim.y)
        sh_pfxs_banked[i][threadIdx.x] = 0;

    __syncthreads();

    int blksz = blockDim.x * blockDim.y;
    int cap = nitems * (blockIdx.x + 1);

    for (int i = threadIdx.y * 32 + threadIdx.x + nitems * blockIdx.x;
         i < cap; i += blksz) {
        int value = keys[i];
        atomicAdd(&(sh_pfxs_banked[value][threadIdx.x]), 1);
    }

    __syncthreads();

    for (int i = threadIdx.y; i < 256; i += blockDim.y) {
        for (int j = 16; j > 0; j = j >> 1)
            if (j > threadIdx.x)
                sh_pfxs_banked[i][threadIdx.x] += sh_pfxs_banked[i][j+threadIdx.x];
        __syncthreads();
    }

    if (threadIdx.y < 8) {
        int off = threadIdx.y * 32 + threadIdx.x;
        atomicAdd(pfxs + off, sh_pfxs_banked[off][0]);
    }

}

__global__
void prefix_scan_5_0_popc(unsigned char *keys, int nitems, int *pfxs) {
    __shared__ int sh_pfxs[32];

    if (threadIdx.y == 0) sh_pfxs[threadIdx.x] = 0;

    __syncthreads();

    int blksz = blockDim.x * blockDim.y;
    int cap = nitems * (blockIdx.x + 1);

    int sum = 0;

    for (int i = threadIdx.y * 32 + threadIdx.x + nitems * blockIdx.x;
         i < cap; i += blksz) {

        int value = keys[i];
        int test = __ballot(value & 1);
        if (!(threadIdx.x & 1)) test = ~test;

        int popc_res = __ballot(value & 2);
        if (!(threadIdx.x & 2)) popc_res = ~popc_res;
        test &= popc_res;

        popc_res = __ballot(value & 4);
        if (!(threadIdx.x & 4)) popc_res = ~popc_res;
        test &= popc_res;

        popc_res = __ballot(value & 8);
        if (!(threadIdx.x & 8)) popc_res = ~popc_res;
        test &= popc_res;

        popc_res = __ballot(value & 16);
        if (!(threadIdx.x & 16)) popc_res = ~popc_res;
        test &= popc_res;

        sum += __popc(test);
    }

    atomicAdd(sh_pfxs + threadIdx.x + 0,   sum);
    __syncthreads();

    if (threadIdx.y == 0) {
        int off = threadIdx.x;
        atomicAdd(pfxs + off, sh_pfxs[off]);
    }
}


__global__
void prefix_scan_8_0_popc(unsigned char *keys, int nitems, int *pfxs) {
    __shared__ int sh_pfxs[256];

    if (threadIdx.y < 8)
        sh_pfxs[threadIdx.y * 32 + threadIdx.x] = 0;

    __syncthreads();

    int blksz = blockDim.x * blockDim.y;
    int cap = nitems * (blockIdx.x + 1);

    int sum_000 = 0;
    int sum_001 = 0;
    int sum_010 = 0;
    int sum_011 = 0;
    int sum_100 = 0;
    int sum_101 = 0;
    int sum_110 = 0;
    int sum_111 = 0;

    for (int i = threadIdx.y * 32 + threadIdx.x + nitems * blockIdx.x;
         i < cap; i += blksz) {

        int value = keys[i];
        int test_000 = __ballot(value & 1);
        if (!(threadIdx.x & 1)) test_000 = ~test_000;

        int popc_res = __ballot(value & 2);
        if (!(threadIdx.x & 2)) popc_res = ~popc_res;
        test_000 &= popc_res;

        popc_res = __ballot(value & 4);
        if (!(threadIdx.x & 4)) popc_res = ~popc_res;
        test_000 &= popc_res;

        popc_res = __ballot(value & 8);
        if (!(threadIdx.x & 8)) popc_res = ~popc_res;
        test_000 &= popc_res;

        popc_res = __ballot(value & 16);
        if (!(threadIdx.x & 16)) popc_res = ~popc_res;
        test_000 &= popc_res;

        popc_res = __ballot(value & 32);
        int test_001 = test_000 & popc_res;
        popc_res = ~popc_res;
        test_000 &= popc_res;

        popc_res = __ballot(value & 64);
        int test_010 = test_000 & popc_res;
        int test_011 = test_001 & popc_res;
        popc_res = ~popc_res;
        test_000 &= popc_res;
        test_001 &= popc_res;

        popc_res = __ballot(value & 128);
        int test_100 = test_000 & popc_res;
        int test_101 = test_001 & popc_res;
        int test_110 = test_010 & popc_res;
        int test_111 = test_011 & popc_res;
        popc_res = ~popc_res;
        test_000 &= popc_res;
        test_001 &= popc_res;
        test_010 &= popc_res;
        test_011 &= popc_res;

        sum_000 += __popc(test_000);
        sum_001 += __popc(test_001);
        sum_010 += __popc(test_010);
        sum_011 += __popc(test_011);
        sum_100 += __popc(test_100);
        sum_101 += __popc(test_101);
        sum_110 += __popc(test_110);
        sum_111 += __popc(test_111);
    }

    atomicAdd(sh_pfxs + (threadIdx.x + 0),   sum_000);
    atomicAdd(sh_pfxs + (threadIdx.x + 32),  sum_001);
    atomicAdd(sh_pfxs + (threadIdx.x + 64),  sum_010);
    atomicAdd(sh_pfxs + (threadIdx.x + 96),  sum_011);
    atomicAdd(sh_pfxs + (threadIdx.x + 128), sum_100);
    atomicAdd(sh_pfxs + (threadIdx.x + 160), sum_101);
    atomicAdd(sh_pfxs + (threadIdx.x + 192), sum_110);
    atomicAdd(sh_pfxs + (threadIdx.x + 224), sum_111);

    __syncthreads();

    if (threadIdx.y < 8) {
        int off = threadIdx.y * 32 + threadIdx.x;
        atomicAdd(pfxs + off, sh_pfxs[off]);
    }
}

