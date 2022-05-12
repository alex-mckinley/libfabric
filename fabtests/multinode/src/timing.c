/*
 * Copyright (c) 2022 Intel Corporation. All rights reserved.
 *
 * This software is available to you under a choice of one of two
 * licenses.  You may choose to be licensed under the terms of the GNU
 * General Public License (GPL) Version 2, available from the file
 * COPYING in the main directory of this source tree, or the
 * BSD license below:
 *
 *     Redistribution and use in source and binary forms, with or
 *     without modification, are permitted provided that the following
 *     conditions are met:
 *
 *      - Redistributions of source code must retain the above
 *        copyright notice, this list of conditions and the following
 *        disclaimer.
 *
 *      - Redistributions in binary form must reproduce the above
 *        copyright notice, this list of conditions and the following
 *        disclaimer in the documentation and/or other materials
 *        provided with the distribution.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
 * BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
 * ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 * CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
#include <string.h>
#include <limits.h>
#include <shared.h>
#include <timing.h>
#include <core.h>

extern struct pm_job_info pm_job;

int multi_timer_create(struct multi_timer **timer, int rank)
{
	*timer = malloc(sizeof(*timer));

	(*timer)->rank = rank;
	(*timer)->start = -1;
	(*timer)->end = -1;

	return 0;
}

void multi_timer_start(struct multi_timer *timer)
{
	if (timer && timer->start == -1)
		timer->start = ft_gettime_ns();
}

void multi_timer_stop(struct multi_timer *timer)
{
	if (timer && timer->start != -1 && timer->end == -1)
		timer->end = ft_gettime_ns();
}

int multi_timer_analyze(struct multi_timer **timers, int timer_count)
{
	int i, j, ret = 0;
	int iterations = timer_count / pm_job.num_ranks;
	double total_timers, total_min, total_max, total_sum_time, total_duration;
	long min[iterations];
	long max[iterations];
	long first_start[iterations];
	long last_end[iterations];
	double sum_time[iterations];
	long duration = 0;
	struct multi_timer **gather_timers;
	double iter_timer_count = 0;
	gather_timers = malloc(sizeof(**gather_timers) * 
							pm_job.num_ranks * pm_job.num_ranks);
	total_timers = total_min = total_max = total_sum_time = total_duration = 0;

	for (i = 0; i < iterations; i++) {
		ret = multi_timer_iter_gather(gather_timers, timers, i);
		if (ret < 0)
			goto err;
		if (pm_job.my_rank == 0) {
			for (j = 0; j < pm_job.num_ranks * pm_job.num_ranks; j++) {
				if (gather_timers[j]->start == -1 || gather_timers[j]->end == -1)
					continue;

				iter_timer_count++;
				duration = gather_timers[j]->end - gather_timers[j]->start;
				sum_time[i] += duration;

				if (gather_timers[j]->start < first_start[i])
					first_start[i] = gather_timers[j]->start;
				if (gather_timers[j]->end > last_end[i])
					last_end[i] = gather_timers[j]->end;
				if (duration > max[i])
					max[i] = duration;
				if (duration < min[i])
					min[i] = duration;
			}
			printf("%-14i %14ld %14ld %14ld %14.3f\n",
					i, min[i], max[i], last_end[i] - first_start[i],
					sum_time[i]/iter_timer_count);

			total_min += min[i];
			total_max += max[i];
			total_duration += last_end[i] - first_start[i];
			total_sum_time += sum_time[i];
			total_timers += iter_timer_count;
		}
		pm_barrier();
	}

	if (pm_job.my_rank == 0)
		printf("%-14s %14.3lf %14.3lf %14.3lf %14.3lf\n", "Average",
			total_min/iterations, total_max/iterations,
			total_duration/iterations,
			total_sum_time/total_timers);

err:
	free(gather_timers);
	return ret & 1;
}

int multi_timer_gather(struct multi_timer **all_timer,
				struct multi_timer **timers, int timer_count)
{
	int i, j;
	int ret = 0;
	struct multi_timer *recv_timer;

	if (pm_job.my_rank == 0) {

		for (i = 0; i < timer_count; i++)
			all_timer[i] = timers[i];

		for (i = 1; i < pm_job.num_ranks; i++) {
			for (j = 0; j < timer_count; j++) {
				recv_timer = malloc(sizeof(*recv_timer));
				ret = socket_recv(pm_job.clients[i-1], recv_timer,
						sizeof(*recv_timer), 0);
				if (ret < 0)
					return ret;

				all_timer[i * timer_count + j] = recv_timer;
			}
		}
	} else {
		for (i = 0; i < timer_count; i++) {
			ret = socket_send(pm_job.sock, timers[i],
					sizeof(*recv_timer), 0);
			if (ret < 0)
				return ret;
		}
	}

	return ret;
}

int multi_timer_iter_gather(struct multi_timer **gather_timers,
				struct multi_timer **timers, int iteration)
{
	int j, ret = 0;
	struct multi_timer **iter_timers;

	iter_timers = malloc(sizeof(**iter_timers) * pm_job.num_ranks);
	for (j = 0; j < pm_job.num_ranks; j++)
		iter_timers[j] = timers[j + iteration * pm_job.num_ranks];

	ret = multi_timer_gather(gather_timers, iter_timers, pm_job.num_ranks);
	if (ret < 0)
		printf("gather timer error: %i\n", ret);

	pm_barrier();
	
	free(iter_timers);
	return ret;
}
