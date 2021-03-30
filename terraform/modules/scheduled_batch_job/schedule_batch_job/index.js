'use strict';
const AWS = require('aws-sdk');
exports.handler = (event, context, callback) => {
  console.log('Received event: ', event);
  const params = {
    jobName: '${name}',
    jobDefinition: '${batch_job_definition}',
    jobQueue: '${batch_job_queue}',
    containerOverrides: event.containerOverrides || null,
    parameters: event.parameters || null,
  };
  new AWS.Batch().submitJob(params, (err, data) => {
    if (err) {
      console.error(err);
      const message = 'Error calling SubmitJob for:' + event.jobName;
      console.error(message);
      callback(message);
    } else {
      const jobId = data.jobId;
      console.log('jobId:', jobId);
      callback(null, jobId);
    }
  });
};